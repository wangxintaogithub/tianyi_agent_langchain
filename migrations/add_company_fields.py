"""
Add company_name and contact_person columns to the uploadrecord table.

SQLModel's create_all() does not alter existing tables. Run this against any
database that predates these columns.

Usage:
    uv run python -m migrations.add_company_fields .env
    uv run python -m migrations.add_company_fields .env --apply
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from dotenv import load_dotenv
from sqlalchemy import text
from sqlmodel import Session, create_engine

from utils.core.db import get_connection_url

COLUMNS = ("company_name", "contact_person")


@dataclass
class MigrationStats:
    missing_columns: tuple[str, ...] = ()
    applied: int = 0
    errors: list[str] = ()


def get_missing(engine) -> MigrationStats:
    """Check which columns are missing from the uploadrecord table."""
    with Session(engine) as session:
        # PostgreSQL stores column names in lowercase
        result = session.exec(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'uploadrecord'"
            )
        )
        existing = {row[0] for row in result}
        missing = tuple(c for c in COLUMNS if c not in existing)
        return MigrationStats(missing_columns=missing)


def apply(engine) -> MigrationStats:
    """Add missing columns to the uploadrecord table."""
    stats = MigrationStats()
    with Session(engine) as session:
        for col in get_missing(engine).missing_columns:
            try:
                sql = f"ALTER TABLE uploadrecord ADD COLUMN {col} VARCHAR(255)"
                session.exec(text(sql))
                stats.applied += 1
                print(f"  ✓ Added column: {col}")
            except Exception as e:
                stats.errors.append(f"{col}: {e}")
                print(f"  ✗ Failed to add {col}: {e}")
        session.commit()
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Add company_name and contact_person columns to uploadrecord"
    )
    parser.add_argument("dotenv_path", nargs="?", default=".env")
    parser.add_argument("--apply", action="store_true", help="Apply the migration")
    args = parser.parse_args()

    load_dotenv(args.dotenv_path)
    engine = create_engine(get_connection_url())

    print("检查 uploadrecord 表是否缺少 company_name / contact_person 列...")
    missing = get_missing(engine)
    if not missing.missing_columns:
        print("✅ 所有列已存在，无需迁移")
        return

    print(f"缺少的列: {', '.join(missing.missing_columns)}")

    if not args.apply:
        print("\n使用 --apply 参数来应用迁移")
        return

    print("\n正在应用迁移...")
    stats = apply(engine)
    print(f"\n完成: 添加了 {stats.applied} 列, {len(stats.errors)} 个错误")
    for err in stats.errors:
        print(f"  错误: {err}")


if __name__ == "__main__":
    main()
