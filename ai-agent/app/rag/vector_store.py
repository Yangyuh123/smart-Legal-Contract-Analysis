"""ChromaDB向量存储 - 管理法律文档的向量索引."""
from __future__ import annotations

import logging
import os
from typing import List, Dict, Any, Optional, Union

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.rag.embeddings import DeepSeekEmbeddings

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """
    ChromaDB 向量存储封装。

    提供文档添加、查询、删除等操作，持久化存储法律知识库的向量索引。
    """

    def __init__(
        self,
        collection_name: Optional[str] = None,
        persist_dir: Optional[str] = None,
    ):
        """
        Args:
            collection_name: 集合名称
            persist_dir: 持久化目录路径
        """
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR

        # 确保持久化目录存在
        os.makedirs(self.persist_dir, exist_ok=True)

        # 初始化 ChromaDB 客户端（持久化模式）
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # 初始化自定义嵌入函数
        self._embedding_function = DeepSeekEmbeddings()

        # 创建自定义 EF 适配器
        self._ef = _CustomEmbeddingFunction(self._embedding_function)

        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self._ef,
            metadata={"description": "SmartLegal knowledge base"},
        )

        logger.info(f"ChromaDB initialized: collection='{self.collection_name}', dir='{self.persist_dir}'")

    def add(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None,
    ) -> List[str]:
        """
        添加文档到向量存储。

        Args:
            texts: 文档文本列表
            metadatas: 对应的元数据列表
            ids: 文档ID列表（不提供则自动生成）
            embeddings: 预计算的向量（不提供则自动生成）

        Returns:
            添加的文档ID列表
        """
        if not texts:
            return []

        # 生成ID
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in texts]

        # 确保metadata不为None
        if metadatas is None:
            metadatas = [{} for _ in texts]

        # 过滤掉空文本
        valid_items = [(t, m, i) for t, m, i in zip(texts, metadatas, ids) if t and t.strip()]
        if not valid_items:
            return []

        valid_texts, valid_metadatas, valid_ids = zip(*valid_items)

        try:
            add_kwargs = {
                "documents": list(valid_texts),
                "metadatas": list(valid_metadatas),
                "ids": list(valid_ids),
            }

            if embeddings:
                add_kwargs["embeddings"] = embeddings

            self.collection.add(**add_kwargs)
            logger.info(f"Added {len(valid_texts)} documents to collection '{self.collection_name}'")
            return list(valid_ids)

        except Exception as e:
            msg = str(e).lower()
            # 兼容历史数据：旧集合可能由失效的嵌入(维度不一致)构建，
            # 检测到维度冲突时自动重建集合后重试一次。
            if "dimension" in msg or "embedding" in msg:
                logger.warning(
                    f"Embedding dimension mismatch detected, rebuilding collection: {e}"
                )
                try:
                    self.delete_collection()
                    self.collection.add(
                        documents=list(valid_texts),
                        metadatas=list(valid_metadatas),
                        ids=list(valid_ids),
                    )
                    logger.info("Collection rebuilt and documents re-added successfully.")
                    return list(valid_ids)
                except Exception as e2:
                    logger.error(f"Failed to rebuild collection: {e2}")
                    raise
            logger.error(f"Failed to add documents: {e}")
            raise

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
        include_embeddings: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        查询相似文档。

        Args:
            query_text: 查询文本
            top_k: 返回最相似的top_k条结果
            where: 元数据过滤条件
            include_embeddings: 是否包含embedding向量

        Returns:
            匹配结果列表: [{"id": str, "text": str, "metadata": dict, "distance": float}, ...]
        """
        if not query_text or not query_text.strip():
            return []

        try:
            include = ["documents", "metadatas", "distances"]
            if include_embeddings:
                include.append("embeddings")

            # 手动嵌入查询文本，避免 ChromaDB 1.5.x 内部 embed_query 兼容问题
            query_embedding = self._ef._embeddings.embed_query(query_text)

            kwargs = {
                "query_embeddings": [query_embedding],
                "n_results": top_k,
                "include": include,
            }
            if where:
                kwargs["where"] = where

            results = self.collection.query(**kwargs)

            # 转换为更友好的格式
            formatted = []
            if results and results.get("ids") and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    item = {
                        "id": doc_id,
                        "text": results["documents"][0][i] if results.get("documents") else "",
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "distance": results["distances"][0][i] if results.get("distances") else 0.0,
                        "score": 1.0 - float(results["distances"][0][i]) if results.get("distances") else 0.0,
                    }
                    formatted.append(item)

            logger.debug(f"Query returned {len(formatted)} results, top_k={top_k}")
            return formatted

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []

    def delete(self, ids: List[str]) -> bool:
        """
        删除指定ID的文档。

        Args:
            ids: 要删除的文档ID列表

        Returns:
            是否删除成功
        """
        if not ids:
            return True

        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents from collection")
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False

    def delete_collection(self) -> bool:
        """删除整个集合."""
        try:
            self.client.delete_collection(self.collection_name)
            logger.info(f"Deleted collection '{self.collection_name}'")
            # 重新创建空集合
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self._ef,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False

    def count(self) -> int:
        """获取集合中的文档数量."""
        try:
            return self.collection.count()
        except Exception:
            return 0

    def get_all_ids(self) -> List[str]:
        """获取集合中所有文档ID."""
        try:
            result = self.collection.get(include=[])
            return result.get("ids", [])
        except Exception:
            return []

    def reset(self):
        """重置集合（删除所有数据后重建）."""
        try:
            self.client.reset()
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self._ef,
            )
            logger.info("Vector store reset complete")
        except Exception as e:
            logger.error(f"Reset failed: {e}")


class _CustomEmbeddingFunction:
    """适配器：将DeepSeekEmbeddings包装为ChromaDB可用的EmbeddingFunction."""

    def __init__(self, embeddings: DeepSeekEmbeddings):
        self._embeddings = embeddings

    def name(self) -> str:
        """返回嵌入函数名称（ChromaDB要求）."""
        model = getattr(self._embeddings, "model_name", "local")
        # 归一化为合法标识符
        safe = str(model).split("/")[-1].replace(".", "-")
        return f"st-{safe}"

    def __call__(self, input: List[str]) -> List[List[float]]:
        """ChromaDB要求的接口."""
        return self._embeddings.embed_documents(input)

    def embed_query(self, text: str = None, input: str = None) -> List[float]:
        """ChromaDB查询时需要的单文本嵌入."""
        query_text = text or input or ''
        return self._embeddings.embed_query(query_text)


# 模块级单例
_vector_store: Optional[ChromaVectorStore] = None


def get_vector_store(collection_name: Optional[str] = None) -> ChromaVectorStore:
    """获取或创建向量存储单例."""
    global _vector_store
    if _vector_store is None:
        _vector_store = ChromaVectorStore(collection_name=collection_name)
    return _vector_store
