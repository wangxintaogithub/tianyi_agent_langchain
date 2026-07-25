"""
LLM 模型配置 - DeepSeek
"""
import os
from dotenv import load_dotenv

load_dotenv()


def get_deepseek_chat(temperature: float | None = None, max_tokens: int | None = None):
    """获取 DeepSeek 聊天模型实例"""
    from langchain_deepseek import ChatDeepSeek

    return ChatDeepSeek(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com"),
        temperature=temperature if temperature is not None else float(os.getenv("TEMPERATURE", "0.7")),
        max_tokens=max_tokens if max_tokens is not None else int(os.getenv("MAX_TOKENS", "2048")),
        verbose=os.getenv("VERBOSE", "false").lower() == "true",
    )
