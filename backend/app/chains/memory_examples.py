"""
记忆管理示例 - PostgreSQL 持久化 vs 内存管理

PostgreSQL 版本（推荐）：
  - run_buffer_memory()   ←  生产环境首选
  - run_summary_memory()  ←  演示手动构建历史

内存版本（仅用于快速测试）：
  - run_manual_history()  ←  演示 InMemoryChatMessageHistory
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_postgres import PostgresChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from app.models.llm import get_deepseek_chat
from app.database import get_sync_connection

# ============================================================
# PostgreSQL 持久化版本（生产推荐）
# ============================================================

CHAT_HISTORY_TABLE = "chat_histories"

# 全局数据库连接（与 conversation_chain.py 共享表）
_connection = get_sync_connection()
PostgresChatMessageHistory.create_tables(_connection, CHAT_HISTORY_TABLE)


def get_session_history_pg(session_id: str) -> PostgresChatMessageHistory:
    """获取 PostgreSQL 持久化的会话历史"""
    return PostgresChatMessageHistory(
        CHAT_HISTORY_TABLE,
        session_id,
        sync_connection=_connection,
    )


def run_buffer_memory():
    """缓冲记忆 - PostgreSQL 持久化，RunnableWithMessageHistory 自动管理"""
    llm = get_deepseek_chat()

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个友好的 AI 助手。"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])
    chain = prompt | llm | StrOutputParser()

    chain_with_history = RunnableWithMessageHistory(
        chain,
        get_session_history_pg,
        input_messages_key="input",
        history_messages_key="history",
    )

    print("\n=== 缓冲记忆 (PostgreSQL 持久化) ===")
    for text in ["我叫小红", "我喜欢画画", "还记得我叫什么吗？"]:
        print(f"[用户]: {text}")
        result = chain_with_history.invoke(
            {"input": text},
            config={"configurable": {"session_id": "buffer_session"}},
        )
        print(f"[AI]: {result[:60]}...")

    history = get_session_history_pg("buffer_session")
    print(f"记忆中的消息数: {len(history.messages)}（已持久化到 PostgreSQL）")


def run_summary_memory():
    """
    摘要记忆示例 - 使用 PostgresChatMessageHistory 手动构建历史
    （替代已弃用的 ConversationSummaryMemory）
    """
    history = PostgresChatMessageHistory(
        CHAT_HISTORY_TABLE,
        "summary_demo_session",
        sync_connection=_connection,
    )
    history.add_user_message("你好，我是张三")
    history.add_ai_message("你好张三！")
    history.add_user_message("我喜欢编程和跑步")
    history.add_ai_message("很好！")
    history.add_user_message("你能记住我的信息吗？")
    history.add_ai_message("当然！")

    print("\n=== PostgresChatMessageHistory 手动管理 ===")
    print(f"历史消息数: {len(history.messages)}（已持久化到 PostgreSQL）")
    for msg in history.messages:
        print(f"  [{msg.type}]: {msg.content[:60]}")


def run_manual_history():
    """手动管理对话历史 - InMemoryChatMessageHistory（仅内存，不持久化）"""
    history = InMemoryChatMessageHistory()

    print("\n=== 手动管理对话历史 (InMemory) ===")
    history.add_user_message("今天天气怎么样？")
    history.add_ai_message("抱歉，我没有天气预报功能。")
    history.add_user_message("那给我讲个笑话吧。")
    history.add_ai_message("为什么程序员总是分不清万圣节和圣诞节？因为 Oct 31 == Dec 25！")
    history.add_user_message("哈哈，有意思")

    print(f"历史消息数: {len(history.messages)}（仅内存，关闭即丢失）")
    for msg in history.messages:
        print(f"  [{msg.type}]: {msg.content[:60]}")
