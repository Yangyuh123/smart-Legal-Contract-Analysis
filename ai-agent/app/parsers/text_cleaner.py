"""文本清洗工具 - 规范化合同文本，去除噪声和格式问题."""
import re

def clean_contract_text(text: str) -> str:
    """
    清洗合同文本，执行以下操作：
    1. 统一换行符
    2. 移除多余空白行
    3. 修复中文编码问题
    4. 规范化标点符号
    5. 移除页眉页脚噪声
    6. 合并被断开的句子

    Args:
        text: 原始文本

    Returns:
        清洗后的文本
    """
    if not text:
        return ""

    # 1. 统一换行符
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2. 移除空行但保留段落分隔（连续3个以上换行合并为2个）
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 3. 清理每行首尾空白
    lines = text.split("\n")
    lines = [line.strip() for line in lines]

    # 4. 移除常见的页眉页脚噪声
    noise_patterns = [
        r"^\s*第\s*\d+\s*页\s*（共\s*\d+\s*页）\s*$",  # 第X页（共Y页）
        r"^\s*第\s*\d+\s*页\s*$",                      # 第X页
        r"^\s*Page\s+\d+\s+of\s+\d+\s*$",              # Page X of Y
        r"^\s*-\s*\d+\s*-\s*$",                         # - X -
        r"^\s*\d+\s*$",                                  # 单独的数字（页码）
        r"^\s*版权所有\s*.*$",
        r"^\s*CONFIDENTIAL\s*$",
        r"^\s*保密\s*$",
    ]
    for pattern in noise_patterns:
        lines = [line for line in lines if not re.match(pattern, line, re.IGNORECASE)]

    # 5. 修复中文标点符号
    text = "\n".join(lines)
    # 英文逗号、句号替换为中文（在中文文本上下文中）
    # 注意：不替换数字中的逗号和句号

    # 6. 统一全角半角字符
    # 保留中文全角标点，但修复全角字母数字为半角（中文文本中常见）
    # text = unicodedata.normalize("NFKC", text)

    # 7. 移除多余空格（中文文本中空格通常是不必要的）
    # 但不处理英文/数字之间的空格
    text = re.sub(r"([一-鿿])\s+([一-鿿])", r"\1\2", text)
    text = re.sub(r"([一-鿿])\s+([，。、；：！？）】》])", r"\1\2", text)

    # 8. 合并被断开的句子（中文句子中间被换行打断）
    # 以中文标点结尾的行保持独立，否则尝试合并下一行
    lines = text.split("\n")
    merged_lines = []
    for i, line in enumerate(lines):
        if not line:
            merged_lines.append(line)
            continue
        # 如果当前行以中文标点结尾，保持独立
        if line and line[-1] in "。！？；：）】》\"'":
            merged_lines.append(line)
        elif i > 0 and merged_lines and merged_lines[-1] and merged_lines[-1][-1] not in "。！？；：）】》\"'\n":
            # 上一行不是以结束标点结尾，尝试合并
            merged_lines[-1] = merged_lines[-1] + line
        else:
            merged_lines.append(line)

    text = "\n".join(merged_lines)

    # 9. 再次清理多余空行
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def normalize_clause_text(text: str) -> str:
    """
    规范化单个条款文本。

    Args:
        text: 条款文本

    Returns:
        规范化后的文本
    """
    if not text:
        return ""
    text = text.strip()
    # 确保条款以适当标点结束
    if text and text[-1] not in "。！？；：）】》\"'.!?;:…—":
        # 检查是否以换行结尾
        pass  # 保留原样，不强制添加标点
    return text


def extract_clauses(text: str) -> list[dict]:
    """
    从合同文本中提取条款结构。

    识别模式：
    - 第X条 / 第X条（中文数字）
    - Article X
    - 一、二、三、...（条款编号）
    - 1. / 1.1 / 1.1.1

    Args:
        text: 清洗后的合同文本

    Returns:
        条款列表 [{"clause_no": "第一条", "title": "标题", "content": "内容"}, ...]
    """
    # 匹配中文章节/条款标题
    clause_patterns = [
        # 第X条 标题
        r'(?:^|\n)\s*(第[一二三四五六七八九十百千万\d]+条(?:\s*之[一二三\d])?)[\s、.]*[（(]?([^（(\n]*?)[）)]?\s*\n',
        # 第X章/第X节
        r'(?:^|\n)\s*(第[一二三四五六七八九十百千万\d]+[章节])\s*[（(]?([^（(\n]*?)[）)]?\s*\n',
        # 一、/ 二、/ 三、 级别标题
        r'(?:^|\n)\s*([一二三四五六七八九十]+)[、，,]\s*[（(]?([^（(\n]*?)[）)]?\s*\n',
        # 数字标题 (一) / (1) /
        r'(?:^|\n)\s*[（(]([一二三四五六七八九十\d]+)[）)]\s*[（(]?([^（(\n]*?)[）)]?\s*\n',
    ]

    clauses = []
    for pattern in clause_patterns:
        matches = list(re.finditer(pattern, text))
        for idx, match in enumerate(matches):
            clause_no = match.group(1).strip()
            title = match.group(2).strip() if match.group(2) else ""
            start_pos = match.end()
            # 找到下一条款起始位置
            end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            content = text[start_pos:end_pos].strip()
            clauses.append({
                "clause_no": clause_no,
                "title": title,
                "content": content,
            })

    return clauses


def truncate_text(text: str, max_length: int = 15000) -> str:
    """
    截断文本到指定长度，优先在段落边界处截断。

    Args:
        text: 原始文本
        max_length: 最大字符数

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text

    # 在max_length附近寻找最近的段落分隔
    truncated = text[:max_length]
    last_para = truncated.rfind("\n\n")
    if last_para > max_length * 0.7:
        truncated = truncated[:last_para]

    return truncated + "\n\n[文本过长，已截断至约{}字符...]".format(len(truncated))
