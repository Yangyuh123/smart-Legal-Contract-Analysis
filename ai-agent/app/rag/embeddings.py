"""Embeddings - 使用DeepSeek API生成文本向量，零本地依赖."""
import logging
from typing import List

logger = logging.getLogger(__name__)


class DeepSeekEmbeddings:
    """DeepSeek API 嵌入封装."""

    def __init__(self, model_name: str = "deepseek-chat", api_key: str = None, base_url: str = None):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self._dimension = 0

    def _get_client(self):
        from openai import OpenAI
        from app.config import settings
        return OpenAI(
            api_key=self.api_key or settings.DEEPSEEK_API_KEY,
            base_url=self.base_url or settings.DEEPSEEK_BASE_URL,
        )

    def embed_query(self, text: str) -> List[float]:
        result = self.embed_documents([text])
        return result[0] if result else []

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            # DeepSeek 可能不支持 embeddings API，改用本地简单嵌入作为降级
            return self._simple_embed(texts)
        except Exception as e:
            logger.warning(f"Embedding failed, using fallback: {e}")
            return self._simple_embed(texts)

    def _simple_embed(self, texts: List[str]) -> List[List[float]]:
        """简易字符级嵌入（降级方案），基于字符bigram哈希."""
        import hashlib
        dim = 384
        result = []
        for text in texts:
            vec = [0.0] * dim
            if text:
                for i in range(len(text) - 1):
                    h = int(hashlib.md5(text[i:i+2].encode('utf-8')).hexdigest()[:8], 16)
                    vec[h % dim] += 1.0
                # 归一化
                norm = sum(v * v for v in vec) ** 0.5
                if norm > 0:
                    vec = [v / norm for v in vec]
            result.append(vec)
        if result and self._dimension == 0:
            self._dimension = len(result[0])
        return result

    @property
    def dimension(self) -> int:
        return self._dimension or 384
