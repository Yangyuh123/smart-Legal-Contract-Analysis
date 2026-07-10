"""混合检索器 - 结合向量检索（稠密）和BM25（稀疏）进行混合检索."""
from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional

from rank_bm25 import BM25Okapi

from app.rag.embeddings import DeepSeekEmbeddings
from app.rag.vector_store import ChromaVectorStore, get_vector_store
from app.rag.text_splitter import split_legal_text

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    混合检索器。

    将稠密向量检索（语义相似度）和BM25稀疏检索（关键词匹配）的结果
    进行融合排序，提供更准确的文档检索。

    融合策略：加权倒数排名融合（RRF - Reciprocal Rank Fusion）
    """

    def __init__(
        self,
        vector_store: Optional[ChromaVectorStore] = None,
        dense_weight: Optional[float] = None,
        sparse_weight: Optional[float] = None,
        top_k: Optional[int] = None,
    ):
        """
        Args:
            vector_store: 向量存储实例
            dense_weight: 稠密检索权重（默认取配置）
            sparse_weight: BM25稀疏检索权重（默认取配置）
            top_k: 最终返回的文档数（默认取配置）
        """
        from app.config import settings

        self.vector_store = vector_store or get_vector_store()
        self.dense_weight = dense_weight if dense_weight is not None else settings.RAG_DENSE_WEIGHT
        self.sparse_weight = sparse_weight if sparse_weight is not None else settings.RAG_SPARSE_WEIGHT
        self.top_k = top_k if top_k is not None else settings.RAG_TOP_K
        self.use_hybrid = settings.USE_HYBRID_RETRIEVAL

        self._dense_embeddings = DeepSeekEmbeddings()

        # BM25索引
        self._bm25_index: Optional[BM25Okapi] = None
        self._bm25_texts: List[str] = []
        self._bm25_metadata: List[Dict[str, Any]] = []

    def build_bm25_index(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None):
        """
        构建BM25索引（用于稀疏检索）。

        Args:
            texts: 文档文本列表
            metadatas: 对应的元数据
        """
        if not texts:
            return

        # 对中文文本进行分词（简单字符级tokenization，适用于中文法律文本）
        tokenized = [self._tokenize(text) for text in texts]

        self._bm25_index = BM25Okapi(tokenized)
        self._bm25_texts = texts
        self._bm25_metadata = metadatas or [{} for _ in texts]
        logger.info(f"BM25 index built with {len(texts)} documents")

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        use_hybrid: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        执行混合检索。

        Args:
            query: 查询文本
            top_k: 返回结果数
            filters: 元数据过滤条件
            use_hybrid: 是否启用混合检索（False时仅使用稠密向量检索）

        Returns:
            检索结果列表: [{"text": str, "metadata": dict, "score": float, "source": "dense"|"sparse"|"hybrid"}, ...]
        """
        k = top_k or self.top_k

        if not query or not query.strip():
            return []

        # 1) 稠密向量检索
        try:
            dense_results = self.vector_store.query(
                query_text=query,
                top_k=k,
                where=filters,
            )
        except Exception as e:
            logger.warning(f"Dense retrieval failed: {e}")
            dense_results = []

        for item in dense_results:
            item.setdefault("source", "dense")

        # 未启用混合检索，直接返回稠密结果
        if not use_hybrid or not self.use_hybrid:
            return dense_results[:k]

        # 2) BM25 稀疏检索（索引为空时，尝试从向量库懒加载重建）
        if not self._bm25_index or not self._bm25_texts:
            self._sync_bm25_from_store()

        sparse_results = self._bm25_search(query, top_k=k)

        # 稀疏检索无结果时退化为稠密结果
        if not sparse_results:
            return dense_results[:k]

        # 3) RRF 融合排序
        fused = self._reciprocal_rank_fusion(dense_results, sparse_results)
        logger.debug(
            f"Hybrid retrieval: dense={len(dense_results)}, "
            f"sparse={len(sparse_results)}, fused={len(fused)}"
        )
        return fused[:k]

    def retrieve_with_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        检索并返回格式化的上下文文本（用于注入LLM提示词）。

        Args:
            query: 查询文本
            top_k: 返回结果数
            filters: 过滤条件

        Returns:
            格式化后的上下文字符串
        """
        results = self.retrieve(query, top_k=top_k, filters=filters)

        if not results:
            return "未找到相关法律参考资料。"

        context_parts = []
        for i, item in enumerate(results):
            text = item.get("text", item.get("raw_text", ""))
            metadata = item.get("metadata", {})
            source = metadata.get("file_name", metadata.get("source", "未知来源"))
            score = item.get("score", 0)

            context_parts.append(
                f"【参考资料 {i + 1}】（来源: {source}, 相关度: {score:.2f}）\n{text}\n"
            )

        return "\n".join(context_parts)

    def index_documents(self, documents: List[Dict[str, Any]]) -> int:
        """
        索引文档到向量存储和BM25。

        Args:
            documents: 文档列表，每个包含 full_text 和可选的 metadata

        Returns:
            索引的chunk总数
        """
        from app.rag.text_splitter import LegalTextSplitter

        splitter = LegalTextSplitter()
        chunks = splitter.split_documents(documents)

        if not chunks:
            return 0

        # 添加到向量存储
        texts = [c["text"] for c in chunks]
        metadatas = [c.get("metadata", {}) for c in chunks]
        ids = self.vector_store.add(texts=texts, metadatas=metadatas)

        # 同步更新BM25索引
        self._sync_bm25_from_store()

        logger.info(f"Indexed {len(ids)} chunks from {len(documents)} documents")
        return len(ids)

    def _bm25_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """BM25稀疏检索."""
        if not self._bm25_index or not self._bm25_texts:
            return []

        tokenized_query = self._tokenize(query)
        scores = self._bm25_index.get_scores(tokenized_query)

        # 获取top_k结果
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        top_indices = indexed_scores[:top_k]

        results = []
        max_score = indexed_scores[0][1] if indexed_scores else 1.0

        for idx, score in top_indices:
            if score <= 0:
                continue
            normalized_score = score / max_score if max_score > 0 else 0.0
            results.append({
                "text": self._bm25_texts[idx],
                "metadata": self._bm25_metadata[idx] if idx < len(self._bm25_metadata) else {},
                "score": normalized_score,
                "bm25_score": score,
                "source": "sparse",
                "index": idx,
            })

        return results

    def _reciprocal_rank_fusion(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        k: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        倒数排名融合（RRF）。

        对稠密和稀疏检索结果进行融合排序。

        Args:
            dense_results: 稠密检索结果
            sparse_results: 稀疏检索结果
            k: RRF平滑常数

        Returns:
            融合后的排序结果
        """
        # 使用文本内容作为键来匹配文档
        rrf_scores: Dict[str, Dict[str, Any]] = {}

        # 处理稠密结果
        for rank, item in enumerate(dense_results):
            key = item.get("text", "")
            rrf_scores[key] = {
                **item,
                "rrf_score": self.dense_weight / (k + rank + 1),
                "dense_rank": rank + 1,
                "sparse_rank": -1,
            }

        # 处理稀疏结果
        for rank, item in enumerate(sparse_results):
            key = item.get("text", "")
            if key in rrf_scores:
                rrf_scores[key]["rrf_score"] += self.sparse_weight / (k + rank + 1)
                rrf_scores[key]["sparse_rank"] = rank + 1
                rrf_scores[key]["source"] = "hybrid"
            else:
                rrf_scores[key] = {
                    **item,
                    "rrf_score": self.sparse_weight / (k + rank + 1),
                    "dense_rank": -1,
                    "sparse_rank": rank + 1,
                    "source": "sparse",
                }

        # 按RRF分数排序
        sorted_items = sorted(
            rrf_scores.values(),
            key=lambda x: x.get("rrf_score", 0),
            reverse=True,
        )

        # 更新最终分数
        for item in sorted_items:
            item["score"] = item["rrf_score"]

        return sorted_items[:self.top_k]

    def _sync_bm25_from_store(self):
        """从向量存储同步数据重建BM25索引."""
        try:
            all_ids = self.vector_store.get_all_ids()
            if not all_ids:
                return

            # 获取所有文档
            result = self.vector_store.collection.get(
                ids=all_ids,
                include=["documents", "metadatas"],
            )

            texts = result.get("documents", [])
            metadatas = result.get("metadatas", [])

            if texts:
                self.build_bm25_index(texts, metadatas)
                logger.info(f"BM25 index synced with {len(texts)} documents")
        except Exception as e:
            logger.error(f"Failed to sync BM25 index: {e}")

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """
        对中文法律文本进行简单分词。

        使用字符级+双字符组合作为tokens，适配BM25的中文处理。
        """
        if not text:
            return []

        # 按非字母数字中文字符分割
        import re
        # 提取所有中文字符、英文单词和数字
        tokens = re.findall(r"[一-鿿]|[a-zA-Z]+|\d+", text)

        # 生成双字组合（bigrams for Chinese）
        bigrams = []
        chinese_chars = [t for t in tokens if len(t) == 1 and "一" <= t <= "鿿"]
        for i in range(len(chinese_chars) - 1):
            bigrams.append(chinese_chars[i] + chinese_chars[i + 1])

        return tokens + bigrams


# 模块级单例
_retriever: Optional[HybridRetriever] = None


def get_retriever() -> HybridRetriever:
    """获取或创建混合检索器单例."""
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever
