"""
对话链 - PostgreSQL 持久化对话历史

使用 PostgresChatMessageHistory 替代 InMemoryChatMessageHistory，
对话记录持久化到 PostgreSQL，服务重启不丢失。

前置条件：
1. PostgreSQL 16+ 已安装并运行
2. 数据库已创建（默认: langchain_db）
3. 表结构由 PostgresChatMessageHistory.create_tables() 自动创建
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_postgres import PostgresChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from app.models.llm import get_deepseek_chat
from app.database import get_sync_connection

CHAT_HISTORY_TABLE = "chat_histories"

# --- 全局初始化（模块加载时执行一次）---
_connection = get_sync_connection()
PostgresChatMessageHistory.create_tables(_connection, CHAT_HISTORY_TABLE)


def get_session_history(session_id: str) -> PostgresChatMessageHistory:
    """获取 PostgreSQL 持久化的会话历史

    所有会话共享同一个数据库连接，通过 session_id 区分。
    PostgresChatMessageHistory 会自动从 message_store 表加载历史。
    """
    return PostgresChatMessageHistory(
        CHAT_HISTORY_TABLE,
        session_id,
        sync_connection=_connection,
    )


def create_conversation_chain():
    """创建带对话历史的链（RunnableWithMessageHistory 自动管理消息添加）"""
    llm = get_deepseek_chat()

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个乐于助人的 AI 助手。"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])

    chain = prompt | llm | StrOutputParser()

    runnable_with_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )

    return runnable_with_history


def run_conversation_chain():
    """运行对话链示例"""
    chain_with_history = create_conversation_chain()
    session_id = "default_session"

    questions = [
        "你好！我叫小明。",
        "还记得我叫什么名字吗？",
        "LangChain 是什么？",
    ]

    for q in questions:
        print(f"\n[用户]: {q}")
        result = chain_with_history.invoke(
            {"input": q},
            config={"configurable": {"session_id": session_id}},
        )
        print(f"[AI]: {result}")

    history = get_session_history(session_id)
    print(f"\n完整对话历史 ({len(history.messages)} 条消息，已持久化到 PostgreSQL):")
    for msg in history.messages:
        print(f"  [{msg.type}]: {msg.content[:60]}...")
