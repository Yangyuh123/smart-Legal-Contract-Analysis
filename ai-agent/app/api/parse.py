"""文档解析API路由 - 解析上传的合同文件提取结构化内容."""
import logging
import time
import traceback
import os
import base64
import tempfile
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.models.schemas import ParseRequest, ParseResponse, APIResponse
from app.parsers.docx_parser import DocxParser
from app.parsers.pdf_parser import PdfParser
from app.parsers.text_cleaner import clean_contract_text, extract_clauses
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
docx_parser = DocxParser()
pdf_parser = PdfParser()


@router.post("", response_model=APIResponse, summary="解析合同文档")
async def parse_document(request: ParseRequest):
    """
    解析上传的合同文件，提取文本内容和结构化信息。

    支持格式：.pdf, .docx, .txt
    支持方式：文件路径或Base64内容

    解析结果包括：
    - 完整文本
    - 条款列表（识别第X条/Article X等条款结构）
    - 表格数据
    - 文档元数据（页数、作者等）
    """
    start_time = time.time()

    try:
        # 确定文件路径
        if request.file_url:
            file_path = request.file_url
        elif request.file_content:
            content_bytes = base64.b64decode(request.file_content)
            suffix = Path(request.file_name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(content_bytes)
                file_path = tmp.name
        else:
            raise HTTPException(status_code=400, detail="请提供 file_url 或 file_content")

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")

        suffix = Path(request.file_name).suffix.lower()

        if suffix in (".docx", ".doc"):
            parsed = docx_parser.parse(file_path)
            full_text = parsed.get("full_text", "")
            page_count = 0
            tables = parsed.get("tables", [])
        elif suffix == ".pdf":
            parsed = pdf_parser.parse(file_path)
            full_text = parsed.get("full_text", "")
            page_count = parsed.get("page_count", 0)
            tables = parsed.get("tables", [])
        elif suffix in (".txt", ".md"):
            with open(file_path, "r", encoding="utf-8") as f:
                full_text = f.read()
            full_text = clean_contract_text(full_text)
            page_count = 0
            tables = []
        else:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式: {suffix}")

        extract_clauses_flag = True
        extract_tables_flag = True
        if request.parse_options:
            extract_clauses_flag = request.parse_options.get("extract_clauses", True)
            extract_tables_flag = request.parse_options.get("extract_tables", True)

        clauses = extract_clauses(full_text) if extract_clauses_flag else None
        if not extract_tables_flag:
            tables = None

        parse_time = round(time.time() - start_time, 2)

        response = ParseResponse(
            file_name=request.file_name,
            full_text=full_text,
            page_count=page_count,
            clauses=clauses,
            tables=tables,
            parse_time=parse_time,
        )

        logger.info(f"Parsed {request.file_name}: {len(full_text)} chars, {page_count} pages, {parse_time}s")

        return APIResponse(
            code=200,
            message=f"解析完成（{parse_time}秒）",
            data=response.model_dump(),
        )

    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Parse error for {request.file_name}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"文档解析失败: {str(e)}")


@router.post("/upload", response_model=APIResponse, summary="上传并解析合同文件")
async def upload_and_parse(
    file: UploadFile = File(..., description="合同文件（PDF/DOCX/TXT）"),
    extract_clauses_flag: bool = Form(default=True, description="是否提取条款"),
    extract_tables_flag: bool = Form(default=True, description="是否提取表格"),
):
    """直接上传文件并解析（multipart/form-data）."""
    start_time = time.time()

    suffix = Path(file.filename).suffix.lower() if file.filename else ""
    if suffix not in (".pdf", ".docx", ".doc", ".txt", ".md"):
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {suffix}，仅支持 PDF/DOCX/TXT/MD")

    try:
        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)

        safe_filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = os.path.join(upload_dir, safe_filename)

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        if suffix in (".docx", ".doc"):
            parsed = docx_parser.parse(file_path)
            full_text = parsed.get("full_text", "")
            page_count = 0
            tables = parsed.get("tables", []) if extract_tables_flag else None
        elif suffix == ".pdf":
            parsed = pdf_parser.parse(file_path)
            full_text = parsed.get("full_text", "")
            page_count = parsed.get("page_count", 0)
            tables = parsed.get("tables", []) if extract_tables_flag else None
        else:
            full_text = content.decode("utf-8", errors="replace")
            full_text = clean_contract_text(full_text)
            page_count = 0
            tables = None

        clauses = extract_clauses(full_text) if extract_clauses_flag else None
        parse_time = round(time.time() - start_time, 2)

        response = ParseResponse(
            file_name=file.filename or "unknown",
            full_text=full_text,
            page_count=page_count,
            clauses=clauses,
            tables=tables,
            parse_time=parse_time,
        )

        return APIResponse(
            code=200,
            message=f"上传并解析完成（{parse_time}秒）",
            data={
                **response.model_dump(),
                "upload_path": file_path,
            },
        )

    except Exception as e:
        logger.error(f"Upload parse error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"文件上传解析失败: {str(e)}")
