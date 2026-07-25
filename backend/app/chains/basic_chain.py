"""
基础链 - 简单的 LLM 调用
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.models.llm import get_deepseek_chat


def create_basic_chain():
    """创建基础 LLM 链"""
    llm = get_deepseek_chat()

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个有用的 AI 助手，请用简洁的方式回答问题。"),
        ("human", "{input}"),
    ])

    chain = prompt | llm | StrOutputParser()
    return chain


def run_basic_chain():
    """运行基础链示例"""
    chain = create_basic_chain()
    result = chain.invoke({"input": "请用一句话介绍 LangChain 是什么？"})
    print(f"\n=== 基础链结果 ===\n{result}")
    return result
