"""
数据库配置 - 用于 RAG 向量存储
"""
import os
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_DIMENSION = 384  # all-MiniLM-L6-v2 向量维度

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'postgres')}@{os.getenv('DB_HOST', '127.0.0.1')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'langchain_db')}",
)


def _to_pgengine_url(url: str) -> str:
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def get_rag_engine():
    """获取 PGEngine 实例（用于向量存储）"""
    from langchain_postgres import PGEngine
    return PGEngine.from_connection_string(url=_to_pgengine_url(DATABASE_URL))
