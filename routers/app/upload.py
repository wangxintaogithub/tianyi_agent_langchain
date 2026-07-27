"""
文件上传 API - 解析 + COS + 企业微信通知
"""
import io
import re
import os
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from utils.app.services.file_parser import parse_file
from utils.app.services.cos_uploader import upload_file as cos_upload
from utils.app.services.wechat_bot import send_text

router = APIRouter(prefix="/api", tags=["Upload API"])
security = HTTPBearer(auto_error=False)

API_KEY = os.environ.get("API_UPLOAD_KEY", "")


def verify_api_key(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    """验证 API Key（Authorization: Bearer <key>）"""
    if not API_KEY:
        # 未配置 API_KEY 时允许所有请求（兼容旧部署）
        return
    if credentials is None or credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="请在 Authorization 请求头中提供有效的 API Key，格式: Bearer <key>",
            headers={"WWW-Authenticate": "Bearer"},
        )

def _sanitize_for_json(obj):
    """递归地将对象转换为 JSON 可序列化的基本类型"""
    import json
    try:
        json.dumps(obj)
        return obj  # 已经是可序列化的
    except (TypeError, ValueError):
        if isinstance(obj, dict):
            return {k: _sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [_sanitize_for_json(v) for v in obj]
        elif isinstance(obj, Exception):
            return f"[{type(obj).__name__}] {str(obj)[:200]}"
        else:
            return str(obj)


ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx",
    ".xls", ".xlsx", ".csv",
    ".txt", ".md", ".json", ".xml", ".yaml", ".yml", ".log",
    ".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".go", ".rs", ".sh", ".bat",
}
MAX_FILE_SIZE = 50 * 1024 * 1024
MAX_FILES = 20


@router.post("/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    wechat_webhook: str | None = Form(None),
    send_to_wechat: bool = Form(True),
    upload_to_cos: bool = Form(True),
    _auth=Depends(verify_api_key),
):
    """上传并处理多个文件

    - 解析文件内容（PDF/DOCX/Excel/CSV/文本）
    - 可选上传到腾讯云 COS
    - 可选发送处理报告到企业微信群
    """
    import logging
    logger = logging.getLogger("uvicorn.error")

    try:
        if len(files) > MAX_FILES:
            raise HTTPException(status_code=400, detail=f"单次最多上传 {MAX_FILES} 个文件")

        results = []

        for file in files:
            filename = file.filename or "unknown"
            ext = os.path.splitext(filename)[1].lower()

            if ext not in ALLOWED_EXTENSIONS:
                results.append({"filename": filename, "status": "skipped", "reason": f"不支持的文件类型: {ext}"})
                continue

            raw = await file.read()
            if len(raw) > MAX_FILE_SIZE:
                results.append({"filename": filename, "status": "skipped", "reason": "文件超过大小限制 (50MB)"})
                continue

            import io
            file_bytes = io.BytesIO(raw)

            # 1. 解析文件内容
            content = parse_file(file_bytes, filename)
            result: dict = {
                "filename": filename, "ext": ext, "size": len(raw),
                "status": "ok", "content_preview": content[:500], "content_length": len(content),
            }

            # 2. 上传到腾讯云 COS
            if upload_to_cos:
                file_bytes.seek(0)
                cos_result = cos_upload(file_bytes, filename)
                if cos_result["status"] == "ok":
                    result["cos_url"] = cos_result["cos_url"]
                    result["cos_key"] = cos_result["cos_key"]
                else:
                    result["cos_status"] = "failed"
                    result["cos_error"] = cos_result.get("error")

            results.append(result)

        # 3. 发送处理报告到企业微信群
        wechat_resp = None
        if send_to_wechat:
            try:
                from utils.app.services.wechat_bot import send_file_result_summary
                wechat_resp = send_file_result_summary(results, webhook_url=wechat_webhook)
            except Exception as e:
                wechat_resp = {"errcode": -1, "errmsg": str(e)}

        success_count = sum(1 for r in results if r["status"] == "ok")
        skip_count = sum(1 for r in results if r["status"] == "skipped")

        response_data = {
            "total": len(results), "success": success_count, "skipped": skip_count,
            "results": results, "wechat_notify": wechat_resp,
        }

        # 确保返回的数据全部 JSON 可序列化（字符串化所有非基本类型）
        return _sanitize_for_json(response_data)
    except HTTPException:
        raise  # 让 FastAPI 正常处理 HTTPException
    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload error: {type(e).__name__}: {str(e)[:200]}")


# ============================================================
# PDF 工人税解析 - 提取 SALDO FINALE 并发送企业微信通知
# ============================================================


def _extract_saldo_finale(text: str) -> Optional[float]:
    """从 PDF 文本中提取 SALDO FINALE 的数值

    匹配模式如: "SALDO FINALE                    625,58" 或 "SALDO FINALE 625.58"
    """
    # 匹配 "SALDO FINALE" 后面跟任意空白/非数字内容，然后是一个数字
    # 支持千位分隔符和小数点（意大利格式: 逗号为小数点）
    pattern = r'SALDO\s+FINALE[^\d]*([\d\.,]+)'
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        return None

    raw = m.group(1)
    # 意大利数字格式: "1.234,56" -> 1234.56
    # 先去掉千位分隔符的点，再将逗号替换为点
    if ',' in raw:
        # 可能包含千位分隔符: 1.234,56
        raw = raw.replace('.', '')   # 去掉千位分隔符
        raw = raw.replace(',', '.')  # 逗号变小数点
    try:
        return float(raw)
    except ValueError:
        return None


def _build_tax_message(amount: float, month: str = "5") -> str:
    """组装工人税通知消息"""
    amount_str = f"{amount:.2f}".rstrip('0').rstrip('.')
    lines = [
        f"你好 {month}月的工人税是{amount_str}€, 6月16号可以扣吗？",
        "",
        "❗❗确认后请填写一下连接，并确保银行里有足够金额。",
        "🛑未填写表格的，我们将不会进行扣款。",
        "任何变化，请发到微信群里通知我们",
        "https://doc.weixin.qq.com/forms/ANgAZgfMADwAfgABAaTANgSGCr8KcSfFf",
        "",
        "温馨提醒：",
        "",
        "1. 记得每个月的工单必须让员工签字，工资一定要经过银行或者邮局汇款/支票支付。",
        "2. 汇款金额要跟工单金额一致",
    ]
    return "\n".join(lines)


@router.post("/parse-tax-pdf")
async def parse_tax_pdf(
    file: UploadFile = File(...),
    month: str = Query("5", description="月份，如 5"),
    wechat_webhook: Optional[str] = Form(None),
    send_to_wechat: bool = Form(True),
    _auth=Depends(verify_api_key),
):
    """上传工人税 PDF，提取 SALDO FINALE 金额并发送企业微信通知

    Args:
        file: PDF 文件（工人税单）
        month: 月份（默认 5）
        wechat_webhook: 企业微信 Webhook 地址，不传则从环境变量读取
        send_to_wechat: 是否发送企业微信通知（默认 True）
    """
    import logging
    logger = logging.getLogger("uvicorn.error")

    try:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="请上传 PDF 文件")

        raw = await file.read()
        if len(raw) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="文件超过大小限制 (50MB)")

        # 1. 解析 PDF
        try:
            import fitz
            doc = fitz.open(stream=raw, filetype="pdf")
            lines = []
            for page in doc:
                lines.append(page.get_text())
            doc.close()
            pdf_text = "\n".join(lines)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF 解析失败: {e}")

        # 2. 提取 SALDO FINALE
        amount = _extract_saldo_finale(pdf_text)
        if amount is None:
            # 返回解析出的文本以便调试
            return {
                "status": "error",
                "detail": "未找到 SALDO FINALE 字段",
                "pdf_text_preview": pdf_text[:1000],
            }

        # 3. 组装消息并发送企业微信
        message = _build_tax_message(amount, month=month)
        wechat_resp = None
        if send_to_wechat:
            try:
                wechat_resp = send_text(message, webhook_url=wechat_webhook)
            except Exception as e:
                wechat_resp = {"errcode": -1, "errmsg": str(e)}

        return {
            "status": "ok",
            "amount": amount,
            "message": message,
            "wechat_notify": wechat_resp,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Parse tax PDF error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"解析失败: {type(e).__name__}: {str(e)[:200]}")
