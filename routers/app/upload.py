"""
文件上传 API - 解析 + COS + 企业微信通知
"""
import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from utils.app.services.file_parser import parse_file
from utils.app.services.cos_uploader import upload_file as cos_upload

router = APIRouter(prefix="/api", tags=["Upload API"])

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
):
    """上传并处理多个文件

    - 解析文件内容（PDF/DOCX/Excel/CSV/文本）
    - 可选上传到腾讯云 COS
    - 可选发送处理报告到企业微信群
    """
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

    return {
        "total": len(results), "success": success_count, "skipped": skip_count,
        "results": results, "wechat_notify": wechat_resp,
    }
