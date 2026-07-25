"""
LangChain 工程配置管理
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_BASE: str = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2048"))
    VERBOSE: bool = os.getenv("VERBOSE", "false").lower() == "true"

    # PostgreSQL 数据库配置（Docker Compose 内网地址）
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@db:5432/langchain_db",
    )
    # 嵌入模型（用于 RAG 向量化）
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # ---------- 文件上传服务 ----------
    # 腾讯云 COS 对象存储
    TENCENT_COS_SECRET_ID: str = os.getenv("TENCENT_COS_SECRET_ID", "")
    TENCENT_COS_SECRET_KEY: str = os.getenv("TENCENT_COS_SECRET_KEY", "")
    TENCENT_COS_REGION: str = os.getenv("TENCENT_COS_REGION", "ap-guangzhou")
    TENCENT_COS_BUCKET: str = os.getenv("TENCENT_COS_BUCKET", "")

    # 企业微信机器人 Webhook
    WECHAT_WEBHOOK_URL: str = os.getenv("WECHAT_WEBHOOK_URL", "")


settings = Settings()
