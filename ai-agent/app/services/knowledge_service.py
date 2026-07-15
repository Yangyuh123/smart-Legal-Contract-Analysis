"""知识库问答服务 - 基于RAG的法律知识问答（支持SSE流式输出）."""
from __future__ import annotations

import logging
import json
from typing import List, Dict, Any, Optional

from app.services.llm_client import get_llm_client
from app.utils.prompt_templates import (
    KNOWLEDGE_QA_SYSTEM_PROMPT,
    format_knowledge_qa_prompt,
)
from app.rag.retriever import get_retriever
from app.rag.document_loader import DocumentLoader
from app.rag.text_splitter import LegalTextSplitter

logger = logging.getLogger(__name__)


class KnowledgeService:
    """知识库问答服务."""

    def __init__(self):
        self.llm = get_llm_client()
        self.retriever = get_retriever()
        self.loader = DocumentLoader()

    async def qa_stream(
        self,
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        top_k: int = 5,
    ):
        """
        基于知识库的流式问答（SSE格式）。

        流程:
        1. 检索相关知识库文档
        2. 构建包含上下文的提示词
        3. 流式生成回答

        Args:
            question: 用户问题
            conversation_history: 对话历史
            top_k: 检索文档数

        Yields:
            SSE格式的响应文本块
        """
        # 1. RAG检索
        knowledge_context = ""
        try:
            knowledge_context = self.retriever.retrieve_with_context(
                query=question,
                top_k=top_k,
            )
        except Exception as e:
            logger.warning(f"Retrieval failed: {e}")
            knowledge_context = "知识库暂时不可用，无法检索到参考资料。"

        # 2. 构建提示词（context 直接注入 system prompt）
        system_prompt = KNOWLEDGE_QA_SYSTEM_PROMPT.format(context=knowledge_context)
        user_prompt = f"请根据参考资料回答：{question}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        logger.info(f"Knowledge QA: question='{question[:50]}...', top_k={top_k}")

        # 4. 流式输出
        try:
            for chunk in self.llm.chat_completion_stream(
                messages=messages,
                temperature=0.3,
                max_tokens=2048,
            ):
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"QA stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    async def qa(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """
        非流式知识库问答。

        Args:
            question: 用户问题
            top_k: 检索文档数

        Returns:
            问答结果
        """
        # RAG检索
        knowledge_context = ""
        references = []
        try:
            retrieval_results = self.retriever.retrieve(query=question, top_k=top_k)
            knowledge_context = self.retriever.retrieve_with_context(query=question, top_k=top_k)
            references = [
                {
                    "source": r.get("metadata", {}).get("source", "未知来源"),
                    "score": r.get("score", 0),
                    "snippet": (r.get("text", "")[:200] + "...") if len(r.get("text", "")) > 200 else r.get("text", ""),
                }
                for r in retrieval_results
            ]
        except Exception as e:
            logger.warning(f"Retrieval failed: {e}")
            knowledge_context = "知识库暂时不可用。"

        # 构建提示词
        user_prompt = format_knowledge_qa_prompt(
            question=question,
            context=knowledge_context,
        )

        messages = [
            {"role": "system", "content": KNOWLEDGE_QA_SYSTEM_PROMPT.format(context=knowledge_context)},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self.llm.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=2048,
            )
            answer = response.get("content", "")

            return {
                "question": question,
                "answer": answer,
                "references": references,
                "usage": response.get("usage", {}),
            }
        except Exception as e:
            logger.error(f"QA failed: {e}")
            raise RuntimeError(f"知识库问答失败: {e}")

    async def index_files(
        self,
        file_paths: List[str],
        collection_name: Optional[str] = None,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
    ) -> Dict[str, Any]:
        """
        索引文件到知识库。

        流程:
        1. 加载文件（PDF/DOCX/TXT）
        2. 文本分割
        3. 生成向量并存入ChromaDB
        4. 更新BM25索引

        Args:
            file_paths: 文件路径列表
            collection_name: 集合名称
            chunk_size: 分块大小
            chunk_overlap: 重叠大小

        Returns:
            索引结果统计
        """
        # 加载文档
        documents = self.loader.load_batch(file_paths)
        successful = [d for d in documents if d.get("full_text")]
        failed = [d for d in documents if not d.get("full_text")]

        if not successful:
            return {
                "status": "failed",
                "message": "没有成功加载任何文档",
                "total_files": len(file_paths),
                "successful": 0,
                "failed": len(failed),
                "failed_files": [d.get("file_name", "") for d in failed],
                "chunks_indexed": 0,
            }

        # 分割文本
        splitter = LegalTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = splitter.split_documents(successful)

        # 索引到向量存储
        from app.rag.vector_store import get_vector_store
        store = get_vector_store(collection_name=collection_name)

        texts = [c["text"] for c in chunks]
        metadatas = [c.get("metadata", {}) for c in chunks]
        ids = store.add(texts=texts, metadatas=metadatas)

        # 更新混合检索器的BM25索引
        try:
            self.retriever.build_bm25_index(texts, metadatas)
        except Exception as e:
            logger.warning(f"BM25 index update failed: {e}")

        logger.info(f"Indexed {len(ids)} chunks from {len(successful)} files")

        return {
            "status": "success",
            "total_files": len(file_paths),
            "successful": len(successful),
            "failed": len(failed),
            "failed_files": [d.get("file_name", "") for d in failed],
            "chunks_indexed": len(ids),
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        }

    async def search_knowledge(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        搜索知识库（仅检索，不生成回答）。

        Args:
            query: 搜索查询
            top_k: 返回结果数
            filters: 过滤条件

        Returns:
            检索结果列表
        """
        results = self.retriever.retrieve(query=query, top_k=top_k, filters=filters)
        return [
            {
                "text": r.get("text", ""),
                "metadata": r.get("metadata", {}),
                "score": r.get("score", 0),
                "source": r.get("source", "unknown"),
            }
            for r in results
        ]

    async def delete_knowledge(self, file_name: str) -> Dict[str, Any]:
        """
        从知识库中删除指定文件的所有索引。

        Args:
            file_name: 文件名

        Returns:
            删除结果
        """
        from app.rag.vector_store import get_vector_store
        store = get_vector_store()

        # 查找匹配的文档ID
        all_ids = store.get_all_ids()
        result = store.collection.get(ids=all_ids, include=["metadatas"])

        ids_to_delete = []
        for doc_id, metadata in zip(result.get("ids", []), result.get("metadatas", [])):
            if metadata and metadata.get("file_name") == file_name:
                ids_to_delete.append(doc_id)

        if ids_to_delete:
            store.delete(ids_to_delete)
            logger.info(f"Deleted {len(ids_to_delete)} chunks for file: {file_name}")

        return {
            "file_name": file_name,
            "deleted_chunks": len(ids_to_delete),
        }
