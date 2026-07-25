"""
PostgreSQL 数据库连接与工具

使用新版 langchain-postgres (v0.0.14+) API:
- PGEngine 用于向量存储（PGVectorStore），自带连接池
- psycopg3 原生连接用于聊天历史（PostgresChatMessageHistory）
"""
import psycopg
from langchain_postgres import PGEngine
from app.config import settings

# all-MiniLM-L6-v2 的向量维度是 384
# 如果更换嵌入模型，请同步修改此值
EMBEDDING_DIMENSION = 384


def _to_pgengine_url(url: str) -> str:
    """将标准 postgresql:// URL 转为 PGEngine 需要的 postgresql+psycopg:// 格式"""
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def get_engine() -> PGEngine:
    """获取 PGEngine 实例（用于向量存储，自带连接池）"""
    return PGEngine.from_connection_string(url=_to_pgengine_url(settings.DATABASE_URL))


def get_sync_connection() -> psycopg.Connection:
    """获取同步数据库连接（用于聊天历史持久化）"""
    return psycopg.connect(settings.DATABASE_URL)
