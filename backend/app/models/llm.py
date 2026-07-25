"""
LLM 模型封装 - 使用 DeepSeek
"""
from langchain_deepseek import ChatDeepSeek
from app.config import settings


def get_deepseek_chat(**kwargs) -> ChatDeepSeek:
    """获取 DeepSeek 聊天模型"""
    return ChatDeepSeek(
        model=kwargs.get("model", settings.DEEPSEEK_MODEL),
        temperature=kwargs.get("temperature", settings.TEMPERATURE),
        max_tokens=kwargs.get("max_tokens", settings.MAX_TOKENS),
        api_key=kwargs.get("api_key", settings.DEEPSEEK_API_KEY),
        api_base=kwargs.get("api_base", settings.DEEPSEEK_API_BASE),
        verbose=kwargs.get("verbose", settings.VERBOSE),
    )
