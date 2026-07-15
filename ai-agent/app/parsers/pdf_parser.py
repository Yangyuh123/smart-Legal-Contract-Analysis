"""PDF文档解析器 - 使用PyMuPDF (fitz)提取PDF文档的文本和结构信息."""
from __future__ import annotations

import logging
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

import fitz

from app.parsers.text_cleaner import clean_contract_text

logger = logging.getLogger(__name__)


class PdfParser:
    """解析PDF格式的合同文档，支持中文文本提取、表格识别和页眉页脚过滤."""

    def __init__(
        self,
        extract_images: bool = False,
        ocr_enabled: bool = False,
        min_confidence: float = 0.5,
    ):
        """
        Args:
            extract_images: 是否提取文档中的图片
            ocr_enabled: 是否为扫描件启用OCR（需要额外配置Tesseract）
            min_confidence: 文本提取的最低置信度
        """
        self.extract_images = extract_images
        self.ocr_enabled = ocr_enabled
        self.min_confidence = min_confidence

    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        解析PDF文件。

        Args:
            file_path: PDF文件路径

        Returns:
            解析结果字典:
            - file_name: 文件名
            - page_count: 页数
            - full_text: 完整文本
            - pages: 每页的文本内容
            - metadata: PDF元数据
            - tables: 提取的表格数据

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误或损坏
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        if path.suffix.lower() != ".pdf":
            raise ValueError(f"不支持的文件格式: {path.suffix}，仅支持 .pdf")

        try:
            doc = fitz.open(str(path))
        except Exception as e:
            raise ValueError(f"无法打开PDF文件 {file_path}: {e}")

        result: Dict[str, Any] = {
            "file_name": path.name,
            "page_count": len(doc),
            "pages": [],
            "full_text": "",
            "metadata": self._extract_metadata(doc),
            "tables": [],
        }

        all_pages_text = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            # 提取文本
            page_text = self._extract_page_text(page)
            result["pages"].append({
                "page_number": page_num + 1,
                "text": page_text,
                "char_count": len(page_text),
            })
            all_pages_text.append(page_text)

            # 提取表格（如果可用）
            try:
                tables = page.find_tables()
                if tables and tables.tables:
                    for table in tables.tables:
                        table_data = self._extract_table_data(table)
                        if table_data:
                            result["tables"].append({
                                "page": page_num + 1,
                                "data": table_data,
                            })
            except Exception:
                # 某些PDF版本不支持表格提取
                pass

        # 合并所有页面文本
        raw_text = "\n\n".join(all_pages_text)

        # 清洗文本
        result["full_text"] = clean_contract_text(raw_text)

        doc.close()
        return result

    def _extract_page_text(self, page: fitz.Page) -> str:
        """
        从单页提取文本，处理中文编码问题。

        Args:
            page: PyMuPDF Page对象

        Returns:
            提取的页面文本
        """
        # 使用 "text" 模式获取保持布局的文本
        text = page.get_text("text", sort=True)

        if not text.strip():
            # 尝试 "blocks" 模式获取文本块
            blocks = page.get_text("blocks")
            text = "\n".join(
                block[4] for block in blocks
                if block[6] == 0 and block[4].strip()  # type 0 = text
            )

        # 尝试处理扫描件（如果启用OCR）
        if not text.strip() and self.ocr_enabled:
            logger.warning(f"Page {page.number + 1}: No text found, OCR would be needed.")

        # 清理常见PDF提取问题
        text = self._fix_pdf_text_issues(text)

        return text

    def _fix_pdf_text_issues(self, text: str) -> str:
        """
        修复PDF文本提取中的常见问题。

        Args:
            text: 原始提取文本

        Returns:
            修复后的文本
        """
        if not text:
            return ""

        # 修复中文文本被空格分隔的问题
        # PDF提取中文时常在字符间插入空格
        import re

        # 修复中文字符间的空格
        text = re.sub(r"(?<=[一-鿿])\s+(?=[一-鿿])", "", text)

        # 修复中文标点前的空格
        text = re.sub(r"\s+([，。、；：！？）】》\"'])", r"\1", text)

        # 修复中文标点后的空格
        text = re.sub(r"([，。、；：！？（【《])\s+", r"\1", text)

        # 统一连字符
        text = text.replace("–", "-").replace("—", "——")

        # 去除多余空行
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text

    def _extract_metadata(self, doc: fitz.Document) -> Dict[str, Any]:
        """提取PDF元数据."""
        meta = doc.metadata or {}
        return {
            "title": meta.get("title", ""),
            "author": meta.get("author", ""),
            "subject": meta.get("subject", ""),
            "creator": meta.get("creator", ""),
            "producer": meta.get("producer", ""),
            "creation_date": meta.get("creationDate", ""),
            "modification_date": meta.get("modDate", ""),
            "format": meta.get("format", "PDF"),
            "encrypted": doc.is_encrypted if hasattr(doc, "is_encrypted") else False,
            "file_size": os.path.getsize(doc.name) if doc.name else 0,
        }

    def _extract_table_data(self, table) -> List[List[str]]:
        """提取TableFinder检测到的表格数据."""
        try:
            cells = table.extract()
            if cells:
                return [[str(cell) if cell is not None else "" for cell in row] for row in cells]
        except Exception as e:
            logger.debug(f"Table extraction failed: {e}")
        return []

    def parse_text_only(self, file_path: str) -> str:
        """
        仅提取文本内容（快速模式）。

        Args:
            file_path: PDF文件路径

        Returns:
            清洗后的纯文本
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        doc = fitz.open(str(path))
        all_text = []

        for page in doc:
            text = page.get_text("text", sort=True)
            if text.strip():
                all_text.append(text)

        doc.close()

        raw_text = "\n\n".join(all_text)
        return clean_contract_text(raw_text)

    def get_page_count(self, file_path: str) -> int:
        """获取PDF页数."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        doc = fitz.open(str(path))
        count = len(doc)
        doc.close()
        return count

    def extract_text_by_pages(self, file_path: str, start_page: int = 0, end_page: Optional[int] = None) -> str:
        """
        提取指定页码范围文本。

        Args:
            file_path: PDF文件路径
            start_page: 起始页码（0-indexed）
            end_page: 结束页码（0-indexed，不含），None表示到最后一页

        Returns:
            指定范围的文本
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        doc = fitz.open(str(path))
        if end_page is None:
            end_page = len(doc)

        texts = []
        for i in range(max(0, start_page), min(end_page, len(doc))):
            page = doc[i]
            text = page.get_text("text", sort=True)
            if text.strip():
                texts.append(text)

        doc.close()
        return clean_contract_text("\n\n".join(texts))
