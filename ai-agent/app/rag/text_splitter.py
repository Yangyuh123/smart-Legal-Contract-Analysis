"""文本分割器 - 针对法律合同文档的语义级别分块策略."""
from __future__ import annotations

import re
import logging
from typing import List, Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


class LegalTextSplitter:
    """
    法律文本智能分割器。

    采用多层分割策略:
    1. 按条款（第X条/Article X）分割 - 最优
    2. 按章节标题分割
    3. 按段落分割
    4. 按固定长度回退分割（保证每个chunk不超过最大长度）
    """

    # 条款分隔符模式
    CLAUSE_PATTERNS = [
        # 第X条 / 第X条之Y / Article X
        re.compile(r'(?:^|\n)\s*(第[一二三四五六七八九十百千万\d]+条(?:\s*之[一二三\d])?)\s'),
        # 第X章 / 第X节
        re.compile(r'(?:^|\n)\s*(第[一二三四五六七八九十百千万\d]+[章节])\s'),
        # Article X / Section X
        re.compile(r'(?:^|\n)\s*(Article\s+\d+[\s\.])', re.IGNORECASE),
        re.compile(r'(?:^|\n)\s*(Section\s+[\d\.]+\s)', re.IGNORECASE),
        # 一、二、三... 级别标题
        re.compile(r'(?:^|\n)\s*([一二三四五六七八九十]+)[、，,]\s*'),
        # 1. / 2.1 / 3.2.1 编号标题
        re.compile(r'(?:^|\n)\s*(\d+(?:\.\d+)*)\s+[一-鿿A-Z]'),
    ]

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        separators: Optional[List[str]] = None,
        keep_clause_title: bool = True,
    ):
        """
        Args:
            chunk_size: 每个文本块的目标最大长度（字符数）
            chunk_overlap: 相邻块之间的重叠长度
            separators: 自定义分割分隔符列表（优先级从高到低）
            keep_clause_title: 分割时是否保留条款标题
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.keep_clause_title = keep_clause_title

        # 默认分隔符：优先按条款，其次段落，最后句子
        self.separators = separators or [
            "\n第",  # 条款开始
            "\n\n",  # 段落
            "\n",    # 行
            "。",    # 中文句号
            "；",    # 中文分号
            ". ",    # 英文句号
            " ",     # 空格（最后手段）
        ]

    def split_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        将文本分割为语义相关的chunk。

        Args:
            text: 待分割的文本
            metadata: 附加到每个chunk的元数据

        Returns:
            chunk列表: [{"text": "...", "metadata": {...}, "chunk_index": 0}, ...]
        """
        if not text or not text.strip():
            return []

        base_metadata = metadata or {}

        # 第一步：尝试按条款进行语义分割
        clauses = self._split_by_clauses(text)

        if len(clauses) <= 1:
            # 没有找到条款结构，使用标准分割
            chunks = self._split_by_size(text)
        else:
            # 按条款分割后，再对过长的条款进行二次分割
            chunks = []
            for clause in clauses:
                if len(clause) <= self.chunk_size:
                    chunks.append(clause)
                else:
                    sub_chunks = self._split_by_size(clause)
                    chunks.extend(sub_chunks)

        # 构建带元数据的chunk列表
        result = []
        for idx, chunk_text in enumerate(chunks):
            chunk_text = chunk_text.strip()
            if not chunk_text:
                continue

            chunk_metadata = {
                **base_metadata,
                "chunk_index": idx,
                "chunk_size": len(chunk_text),
                "total_chunks": len(chunks),
            }

            result.append({
                "text": chunk_text,
                "metadata": chunk_metadata,
                "chunk_index": idx,
            })

        logger.debug(f"Split text ({len(text)} chars) into {len(result)} chunks")
        return result

    def split_documents(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        批量分割多个文档。

        Args:
            documents: 文档列表，每个包含 full_text 和元数据

        Returns:
            所有chunk的列表
        """
        all_chunks = []

        for doc in documents:
            text = doc.get("full_text", "")
            if not text:
                continue

            doc_metadata = {
                "file_name": doc.get("file_name", ""),
                "file_path": doc.get("file_path", ""),
                "file_type": doc.get("file_type", ""),
                "source": doc.get("file_name", ""),
            }

            chunks = self.split_text(text, metadata=doc_metadata)
            all_chunks.extend(chunks)

        logger.info(f"Split {len(documents)} documents into {len(all_chunks)} total chunks")
        return all_chunks

    def _split_by_clauses(self, text: str) -> List[str]:
        """
        按条款/章节结构分割文本。

        Args:
            text: 合同文本

        Returns:
            按条款分割的文本片段列表
        """
        # 尝试找到所有条款起始位置
        split_positions = []

        for pattern in self.CLAUSE_PATTERNS:
            for match in pattern.finditer(text):
                pos = match.start()
                # 调整到换行符处
                if pos > 0:
                    # 向前找到最近的换行符
                    nl_pos = text.rfind("\n", 0, pos)
                    if nl_pos >= 0:
                        pos = nl_pos
                split_positions.append(pos)

        if not split_positions:
            return [text] if text.strip() else []

        # 去重并排序
        split_positions = sorted(set(split_positions))
        # 过滤过于接近的分割点（至少间隔50字符）
        filtered = [split_positions[0]]
        for pos in split_positions[1:]:
            if pos - filtered[-1] >= 50:
                filtered.append(pos)

        # 按分割点拆分
        clauses = []
        for i, pos in enumerate(filtered):
            start = pos
            end = filtered[i + 1] if i + 1 < len(filtered) else len(text)
            clause_text = text[start:end].strip()
            if clause_text:
                clauses.append(clause_text)

        # 添加分割点之前的文本（如合同标题）
        if filtered and filtered[0] > 0:
            preamble = text[:filtered[0]].strip()
            if preamble:
                clauses.insert(0, preamble)

        return clauses

    def _split_by_size(self, text: str) -> List[str]:
        """
        按固定大小+分隔符回退策略分割文本。

        Args:
            text: 待分割的文本

        Returns:
            文本片段列表
        """
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        chunks = []
        current_chunk = ""

        # 首选用段落分割
        paragraphs = text.split("\n\n")

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 如果添加此段落后不超过chunk_size，则添加
            if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                # 保存当前chunk
                if current_chunk:
                    chunks.append(current_chunk)

                # 如果段落本身就超过限制，需要进一步分割
                if len(para) > self.chunk_size:
                    sub_chunks = self._split_long_paragraph(para)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = para

        # 添加最后一个chunk
        if current_chunk:
            chunks.append(current_chunk)

        # 添加重叠
        if self.chunk_overlap > 0 and len(chunks) > 1:
            overlapped = []
            for i, chunk in enumerate(chunks):
                if i == 0:
                    overlapped.append(chunk)
                else:
                    # 从前一个chunk的尾部取overlap部分的文本
                    prev = chunks[i - 1]
                    if len(prev) > self.chunk_overlap:
                        overlap_text = prev[-self.chunk_overlap:]
                        # 从最近的句子边界截取
                        for sep in ["。", "；", "\n", ". ", "; ", " "]:
                            idx = overlap_text.find(sep)
                            if idx > len(overlap_text) // 2:
                                overlap_text = overlap_text[idx + 1:]
                                break
                        overlapped.append(overlap_text + "\n" + chunk)
                    else:
                        overlapped.append(chunk)
            chunks = overlapped

        return chunks

    def _split_long_paragraph(self, text: str) -> List[str]:
        """
        分割过长的段落。

        Args:
            text: 过长的段落文本

        Returns:
            分割后的文本片段
        """
        chunks = []
        sentences = re.split(r"(?<=[。！？；])(?=[^」』）\)])", text)

        current = ""
        for sent in sentences:
            if len(current) + len(sent) <= self.chunk_size:
                current += sent
            else:
                if current:
                    chunks.append(current.strip())
                # 如果单个句子就超长，硬截断
                if len(sent) > self.chunk_size:
                    for i in range(0, len(sent), self.chunk_size):
                        chunks.append(sent[i:i + self.chunk_size].strip())
                    current = ""
                else:
                    current = sent

        if current.strip():
            chunks.append(current.strip())

        return chunks


def split_legal_text(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> List[Dict[str, Any]]:
    """
    便捷函数：分割法律文本。

    Args:
        text: 待分割文本
        chunk_size: 块大小
        chunk_overlap: 重叠大小

    Returns:
        chunk列表
    """
    splitter = LegalTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)
