"""RAG文档加载器 - 统一加载PDF、DOCX和TXT文件."""
from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.parsers.docx_parser import DocxParser
from app.parsers.pdf_parser import PdfParser
from app.parsers.text_cleaner import clean_contract_text

logger = logging.getLogger(__name__)

# 支持的文件扩展名
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md"}

# 单例解析器实例
_docx_parser = None
_pdf_parser = None


def _get_docx_parser() -> DocxParser:
    global _docx_parser
    if _docx_parser is None:
        _docx_parser = DocxParser()
    return _docx_parser


def _get_pdf_parser() -> PdfParser:
    global _pdf_parser
    if _pdf_parser is None:
        _pdf_parser = PdfParser()
    return _pdf_parser


class DocumentLoader:
    """统一的文档加载器，根据文件类型自动选择合适的解析器."""

    def __init__(self):
        self.supported_extensions = SUPPORTED_EXTENSIONS

    def load(self, file_path: str) -> Dict[str, Any]:
        """
        加载单个文档。

        Args:
            file_path: 文件路径

        Returns:
            加载结果: {
                "file_path": str,
                "file_name": str,
                "file_type": str,
                "full_text": str,
                "page_count": int,
                "metadata": dict,
                "tables": list,
            }

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的格式
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        suffix = path.suffix.lower()
        if suffix not in self.supported_extensions:
            raise ValueError(
                f"不支持的文件格式: {suffix}，支持: {', '.join(sorted(self.supported_extensions))}"
            )

        logger.info(f"Loading document: {file_path}")

        if suffix in (".docx", ".doc"):
            return self._load_docx(file_path)
        elif suffix == ".pdf":
            return self._load_pdf(file_path)
        elif suffix in (".txt", ".md"):
            return self._load_text(file_path)

        raise ValueError(f"未处理的文件类型: {suffix}")

    def load_batch(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        批量加载文档。

        Args:
            file_paths: 文件路径列表

        Returns:
            文档数据列表
        """
        results = []
        for fp in file_paths:
            try:
                result = self.load(fp)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to load {fp}: {e}")
                results.append({
                    "file_path": fp,
                    "file_name": Path(fp).name,
                    "error": str(e),
                    "full_text": "",
                })
        return results

    def _load_docx(self, file_path: str) -> Dict[str, Any]:
        """加载DOCX文档."""
        parser = _get_docx_parser()
        parsed = parser.parse(file_path)
        return {
            "file_path": str(Path(file_path).resolve()),
            "file_name": Path(file_path).name,
            "file_type": "docx",
            "full_text": parsed.get("full_text", ""),
            "page_count": 0,  # DOCX没有固定页数概念
            "metadata": parsed.get("metadata", {}),
            "tables": parsed.get("tables", []),
        }

    def _load_pdf(self, file_path: str) -> Dict[str, Any]:
        """加载PDF文档."""
        parser = _get_pdf_parser()
        parsed = parser.parse(file_path)
        return {
            "file_path": str(Path(file_path).resolve()),
            "file_name": Path(file_path).name,
            "file_type": "pdf",
            "full_text": parsed.get("full_text", ""),
            "page_count": parsed.get("page_count", 0),
            "metadata": parsed.get("metadata", {}),
            "tables": parsed.get("tables", []),
        }

    def _load_text(self, file_path: str) -> Dict[str, Any]:
        """加载纯文本或Markdown文件."""
        path = Path(file_path)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        # 检测编码
        if not text:
            # 尝试其他编码
            for enc in ["gbk", "gb2312", "latin-1"]:
                try:
                    with open(path, "r", encoding=enc) as f:
                        text = f.read()
                    if text:
                        break
                except Exception:
                    continue

        text = clean_contract_text(text)

        return {
            "file_path": str(path.resolve()),
            "file_name": path.name,
            "file_type": path.suffix.lstrip("."),
            "full_text": text,
            "page_count": 0,
            "metadata": {
                "file_size": path.stat().st_size,
            },
            "tables": [],
        }

    @staticmethod
    def is_supported(file_path: str) -> bool:
        """检查文件格式是否受支持."""
        suffix = Path(file_path).suffix.lower()
        return suffix in SUPPORTED_EXTENSIONS

    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """获取文件基本信息，不完整加载."""
        path = Path(file_path)
        return {
            "file_name": path.name,
            "file_type": path.suffix.lower().lstrip("."),
            "file_size": path.stat().st_size if path.exists() else 0,
            "is_supported": DocumentLoader.is_supported(file_path),
        }
