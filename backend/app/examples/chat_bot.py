"""
交互式聊天机器人 - 使用 RunnableWithMessageHistory（官方推荐替代 langchain.memory）
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from app.models.llm import get_deepseek_chat

# 存储不同会话的历史记录
session_histories: dict[str, InMemoryChatMessageHistory] = {}


def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    """获取或创建会话历史"""
    if session_id not in session_histories:
        session_histories[session_id] = InMemoryChatMessageHistory()
    return session_histories[session_id]


def create_chat_bot():
    """创建聊天机器人"""
    llm = get_deepseek_chat(temperature=0.8)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个友好的 AI 聊天助手。请用中文回答，保持对话自然有趣。"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])

    chain = prompt | llm | StrOutputParser()

    chain_with_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )

    return chain_with_history


def run_chat_bot():
    """运行命令行聊天机器人"""
    print("\n" + "=" * 50)
    print("  LangChain 聊天机器人 🤖")
    print("  输入 'exit' 或 'quit' 退出")
    print("=" * 50)

    chain_with_history = create_chat_bot()
    session_id = "chat_session"

    while True:
        try:
            user_input = input("\n[你]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n再见！")
            break

        if user_input.lower() in ("exit", "quit", "退出"):
            print("[AI]: 再见！期待下次聊天~")
            break

        if not user_input:
            continue

        result = chain_with_history.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}},
        )

        print(f"\n[AI]: {result}")

        # RunnableWithMessageHistory 自动管理消息，无需手动 add
        # 这里只做消息数限制
        history = session_histories[session_id]
        if len(history.messages) > 20:
            history.messages = history.messages[-20:]


if __name__ == "__main__":
    run_chat_bot()
