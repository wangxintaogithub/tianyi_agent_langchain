"""
Add uploadrecord table for managing upload API data.

This migration creates the uploadrecord table that stores file upload records,
WeChat send status, email send status, COS upload info, and retry information.

Usage:
    uv run python -m migrations.add_upload_records .env
    uv run python -m migrations.add_upload_records .env --apply
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from dotenv import load_dotenv
from sqlalchemy import text
from sqlmodel import Session, create_engine

from utils.core.db import get_connection_url


@dataclass
class MigrationStats:
    table_exists: bool = False
    created: bool = False


def _table_exists(session: Session, table_name: str) -> bool:
    result = session.connection().execute(
        text(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = :table_name
            """
        ),
        {"table_name": table_name},
    )
    return result.first() is not None


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS uploadrecord (
    id SERIAL PRIMARY KEY,

    -- 文件信息
    filename VARCHAR NOT NULL,
    file_ext VARCHAR NOT NULL,
    file_size INTEGER NOT NULL DEFAULT 0,
    content_preview TEXT,
    content_length INTEGER NOT NULL DEFAULT 0,

    -- 腾讯云 COS 信息
    cos_url VARCHAR,
    cos_key VARCHAR,
    cos_status VARCHAR,
    cos_error VARCHAR,

    -- 税单金额
    tax_amount DOUBLE PRECISION,
    tax_month VARCHAR,

    -- 企业微信发送状态
    wechat_status VARCHAR,
    wechat_error VARCHAR,
    wechat_response TEXT,

    -- 邮件发送状态
    email_status VARCHAR,
    email_error VARCHAR,
    email_recipient VARCHAR,
    email_content TEXT,

    -- 本地文件路径
    file_path VARCHAR,

    -- 上传 API 原始请求信息
    raw_request TEXT,

    -- 重试信息
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_retry_at TIMESTAMP WITHOUT TIME ZONE,
    last_error TEXT,

    -- 时间戳
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_uploadrecord_filename ON uploadrecord (filename);
CREATE INDEX IF NOT EXISTS ix_uploadrecord_created_at ON uploadrecord (created_at);
CREATE INDEX IF NOT EXISTS ix_uploadrecord_wechat_status ON uploadrecord (wechat_status);
"""


def add_upload_records_table(env_file: str, apply: bool) -> MigrationStats:
    load_dotenv(env_file, override=True)
    engine = create_engine(get_connection_url())
    stats = MigrationStats()

    try:
        with Session(engine) as session:
            stats.table_exists = _table_exists(session, "uploadrecord")

            if apply and not stats.table_exists:
                session.connection().execute(text(CREATE_TABLE_SQL))
                session.commit()
                stats.created = True
            else:
                session.rollback()
    finally:
        engine.dispose()

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Add uploadrecord table for tracking file uploads, "
            "WeChat sends, email sends, and retry status. "
            "Without --apply, runs in dry-run mode."
        )
    )
    parser.add_argument("env", help="Env file to use (e.g. .env)")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the schema change (default is dry-run).",
    )
    args = parser.parse_args()

    stats = add_upload_records_table(env_file=args.env, apply=args.apply)
    mode = "APPLY" if args.apply else "DRY-RUN"

    if stats.table_exists:
        print(f"[{mode}] uploadrecord 表已存在，无需操作。")
    elif stats.created:
        print(f"[{mode}] ✅ uploadrecord 表创建成功！")
    else:
        print(f"[{mode}] uploadrecord 表不存在。使用 --apply 参数创建。")


if __name__ == "__main__":
    main()
