"""
Agent 示例 - 使用 DeepSeek + 自定义工具
"""
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.models.llm import get_deepseek_chat
from app.agents.tools import tools


def create_agent(verbose: bool = True):
    """创建 Tool Calling Agent"""
    llm = get_deepseek_chat()

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个智能助手，可以使用工具来帮助用户解决问题。"
                   "请根据需要选择合适的工具并给出友好的回复。"),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,
        handle_parsing_errors=True,
    )
    return agent_executor


def run_simple_agent():
    """运行 Agent 示例"""
    agent = create_agent()

    questions = [
        "现在几点了？",
        "计算 12345 * 6789 等于多少？",
        "请统计这句话的字符数、单词数和行数。",
    ]

    print("\n=== Agent 示例 ===")
    for q in questions:
        print(f"\n[用户]: {q}")
        result = agent.invoke({"input": q})
        print(f"[AI]: {result['output']}")
