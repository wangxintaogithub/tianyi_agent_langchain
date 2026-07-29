"""
上传记录管理页面 - 查看/管理 Upload API 接收的数据
"""
import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, col, desc, or_
from utils.core.dependencies import get_optional_user
from utils.app.models import UploadRecord
from utils.core.models import User
from utils.core.db import get_connection_url, create_engine

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/upload", tags=["Upload Management"])
templates = Jinja2Templates(directory="templates")


def _get_db_session():
    engine = create_engine(get_connection_url())
    return Session(engine)


@router.get("/records")
async def list_upload_records(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=10, le=100),
    status: Optional[str] = Query(None, description="筛选: success/failed/skipped/all"),
    search: Optional[str] = Query(None, description="搜索公司名称/负责人"),
    user: Optional[User] = Depends(get_optional_user),
):
    """上传记录列表页面"""
    db_session = _get_db_session()
    try:
        query = select(UploadRecord)

        # 筛选条件 - 按邮件发送状态
        if status and status != "all":
            if status == "failed":
                query = query.where(UploadRecord.email_status == "failed")
            elif status == "success":
                query = query.where(UploadRecord.email_status == "success")

        if search:
            query = query.where(
                or_(
                    UploadRecord.company_name.ilike(f"%{search}%"),
                    UploadRecord.contact_person.ilike(f"%{search}%"),
                )
            )

        # 按创建时间倒序
        query = query.order_by(desc(UploadRecord.created_at))

        # 分页
        total_query = select(UploadRecord.id)
        if status and status != "all":
            if status == "failed":
                total_query = total_query.where(UploadRecord.email_status == "failed")
            elif status == "success":
                total_query = total_query.where(UploadRecord.email_status == "success")
        if search:
            total_query = total_query.where(
                or_(
                    UploadRecord.company_name.ilike(f"%{search}%"),
                    UploadRecord.contact_person.ilike(f"%{search}%"),
                )
            )

        total = len(db_session.exec(total_query).all())
        total_pages = max(1, (total + per_page - 1) // per_page)

        query = query.offset((page - 1) * per_page).limit(per_page)
        records = db_session.exec(query).all()

        return templates.TemplateResponse(
            request,
            "upload/list.html",
            {
                "user": user,
                "records": records,
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "current_status": status or "all",
                "search": search or "",
            },
        )
    finally:
        db_session.close()


@router.get("/records/{record_id}")
async def view_upload_record(
    request: Request,
    record_id: int,
    user: Optional[User] = Depends(get_optional_user),
):
    """上传记录详情页面"""
    db_session = _get_db_session()
    try:
        record = db_session.get(UploadRecord, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")

        # 解析 wechat_response JSON
        wechat_response_data = None
        if record.wechat_response:
            try:
                wechat_response_data = json.loads(record.wechat_response)
            except (json.JSONDecodeError, TypeError):
                wechat_response_data = record.wechat_response

        return templates.TemplateResponse(
            request,
            "upload/detail.html",
            {
                "user": user,
                "record": record,
                "wechat_response_data": wechat_response_data,
            },
        )
    finally:
        db_session.close()


@router.post("/records/{record_id}/resend-wechat")
async def resend_wechat(
    request: Request,
    record_id: int,
    user: Optional[User] = Depends(get_optional_user),
):
    """重新发送企业微信通知"""
    import os
    from utils.app.services.wechat_bot import send_text, send_file_result_summary

    db_session = _get_db_session()
    try:
        record = db_session.get(UploadRecord, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")

        webhook = os.environ.get("WECHAT_WEBHOOK_URL", "")

        try:
            if record.tax_amount is not None:
                from routers.app.upload import _build_tax_message
                message = _build_tax_message(record.tax_amount, month=record.tax_month or "5")
                resp = send_text(message, webhook_url=webhook)
            else:
                result_item = {
                    "filename": record.filename,
                    "status": "ok",
                    "cos_url": record.cos_url or "",
                }
                resp = send_file_result_summary([result_item], webhook_url=webhook)

            if resp and resp.get("errcode") == 0:
                record.wechat_status = "success"
                record.wechat_error = None
                record.retry_count = (record.retry_count or 0) + 1
                from datetime import datetime, UTC
                record.last_retry_at = datetime.now(UTC).replace(tzinfo=None)
                record.wechat_response = json.dumps(resp, ensure_ascii=False)
                db_session.commit()
                return {"success": True, "message": "企业微信通知已重新发送成功"}
            else:
                err_msg = resp.get("errmsg", "发送失败") if resp else "未知错误"
                record.wechat_status = "failed"
                record.wechat_error = err_msg
                record.retry_count = (record.retry_count or 0) + 1
                from datetime import datetime, UTC
                record.last_retry_at = datetime.now(UTC).replace(tzinfo=None)
                db_session.commit()
                return {"success": False, "message": f"发送失败: {err_msg}"}
        except Exception as e:
            record.wechat_status = "failed"
            record.wechat_error = str(e)
            record.retry_count = (record.retry_count or 0) + 1
            from datetime import datetime, UTC
            record.last_retry_at = datetime.now(UTC).replace(tzinfo=None)
            db_session.commit()
            return {"success": False, "message": f"发送异常: {str(e)}"}
    finally:
        db_session.close()


@router.get("/files/{record_id}")
async def view_uploaded_file(
    request: Request,
    record_id: int,
    user: Optional[User] = Depends(get_optional_user),
):
    """查看上传的原始文件 - 重定向到 COS 链接"""
    from fastapi.responses import RedirectResponse

    db_session = _get_db_session()
    try:
        record = db_session.get(UploadRecord, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")

        if record.cos_url:
            return RedirectResponse(url=record.cos_url)

        raise HTTPException(status_code=404, detail="文件未上传到 COS，无法访问")
    finally:
        db_session.close()


@router.get("/files/{record_id}/preview")
async def preview_uploaded_file(
    request: Request,
    record_id: int,
):
    """代理预览上传的文件（从 COS 拉取并返回，避免 CORS 问题）"""
    import httpx

    db_session = _get_db_session()
    try:
        record = db_session.get(UploadRecord, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")

        if not record.cos_url:
            raise HTTPException(status_code=404, detail="文件未上传到 COS，无法预览")

        # 从 COS 拉取文件并代理返回
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(record.cos_url, follow_redirects=True)
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail="无法从 COS 获取文件")

            content_type = resp.headers.get("content-type", "application/octet-stream")
            # PDF 强制用正确的 MIME 类型以便浏览器内嵌显示
            if record.filename.lower().endswith(".pdf"):
                content_type = "application/pdf"
            elif record.filename.lower().endswith((".doc", ".docx")):
                content_type = "application/msword"

            from fastapi.responses import Response
            return Response(
                content=resp.content,
                media_type=content_type,
                headers={
                    "Content-Disposition": f'inline; filename="{record.filename}"',
                    "Content-Length": str(len(resp.content)),
                    "Access-Control-Allow-Origin": "*",
                },
            )
    finally:
        db_session.close()
