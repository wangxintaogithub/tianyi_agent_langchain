"""
Example application data model.

Replace this module with your own application-specific SQLModel classes.
Any SQLModel table classes defined here will be automatically created in the
database on startup, as long as this module is imported in utils/core/db.py.
"""

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, Text
from utils.core.models import utc_now


# --- Replace the example model below with your own application models ---


class OrganizationResource(SQLModel, table=True):
    """
    Example application data model representing a resource owned by an
    organization. Replace this with your own application-specific models.

    Each resource belongs to a single organization (via organization_id foreign
    key). Users with the READ_ORGANIZATION_RESOURCES permission can view these
    resources, users with WRITE_ORGANIZATION_RESOURCES can create/edit them, and
    users with DELETE_ORGANIZATION_RESOURCES can delete them.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    organization_id: int = Field(
        foreign_key="organization.id", ondelete="CASCADE", index=True
    )
    title: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class UploadRecord(SQLModel, table=True):
    """上传记录 - 记录文件上传、企业微信发送状态和邮件发送状态"""

    id: Optional[int] = Field(default=None, primary_key=True)

    # 文件信息
    filename: str = Field(index=True)
    file_ext: str
    file_size: int = Field(default=0)
    content_preview: Optional[str] = Field(default=None, sa_column=Column(Text))
    content_length: int = Field(default=0)

    # 腾讯云 COS 信息
    cos_url: Optional[str] = None
    cos_key: Optional[str] = None
    cos_status: Optional[str] = None  # "ok" / "failed" / None
    cos_error: Optional[str] = None

    # 税单金额
    tax_amount: Optional[float] = None
    tax_month: Optional[str] = None

    # 企业微信发送状态
    wechat_status: Optional[str] = None  # "success" / "failed" / "skipped"
    wechat_error: Optional[str] = None
    wechat_response: Optional[str] = Field(default=None, sa_column=Column(Text))  # 原始响应

    # 收件人信息
    company_name: Optional[str] = Field(default=None, index=True, description="公司名称")
    contact_person: Optional[str] = Field(default=None, description="负责人/收件人")

    # 邮件发送状态
    email_status: Optional[str] = None  # "success" / "failed" / "skipped"
    email_error: Optional[str] = None
    email_recipient: Optional[str] = None
    email_content: Optional[str] = Field(default=None, sa_column=Column(Text))

    # 本地文件路径（用于预览）
    file_path: Optional[str] = None

    # 上传 API 原始请求信息
    raw_request: Optional[str] = Field(default=None, sa_column=Column(Text))

    # 重试信息
    retry_count: int = Field(default=0)
    last_retry_at: Optional[datetime] = None
    last_error: Optional[str] = Field(default=None, sa_column=Column(Text))

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
