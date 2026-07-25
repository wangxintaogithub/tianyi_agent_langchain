"""
翻译助手 - 多步链实现
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.models.llm import get_deepseek_chat


def run_translator():
    """翻译助手示例 - 翻译 + 校对 + 总结"""
    llm = get_deepseek_chat()

    # 翻译
    translate_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个专业翻译。将以下{source_lang}翻译成{target_lang}，只输出翻译结果。"),
        ("human", "{text}"),
    ])

    # 校对
    review_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个翻译校对专家。检查以下翻译是否准确自然，如果有问题请修正。"),
        ("human", "原文：{source_text}\n翻译：{translated_text}"),
    ])

    chain1 = translate_prompt | llm | StrOutputParser()
    chain2 = review_prompt | llm | StrOutputParser()

    print("\n=== 翻译助手 ===")
    text = "Artificial Intelligence is transforming the way we live and work."
    source_lang = "英文"
    target_lang = "中文"

    translated = chain1.invoke({
        "source_lang": source_lang,
        "target_lang": target_lang,
        "text": text,
    })
    print(f"\n[原文]: {text}")
    print(f"[翻译]: {translated}")

    reviewed = chain2.invoke({
        "source_text": text,
        "translated_text": translated,
    })
    print(f"[校对]: {reviewed}")


def run_text_processor():
    """文本处理管道"""
    llm = get_deepseek_chat()

    # 多个处理步骤
    steps = [
        ("总结", ChatPromptTemplate.from_messages([
            ("system", "用一句话概括以下内容。"),
            ("human", "{text}"),
        ])),
        ("关键词", ChatPromptTemplate.from_messages([
            ("system", "从以下内容中提取 3-5 个关键词，用逗号分隔。"),
            ("human", "{text}"),
        ])),
        ("情感", ChatPromptTemplate.from_messages([
            ("system", "分析以下文本的情感倾向：积极、消极或中性，并给出理由。"),
            ("human", "{text}"),
        ])),
    ]

    text = "LangChain 是一个强大的框架，它简化了 LLM 应用的开发流程。"
    print(f"\n=== 文本处理管道 ===")
    print(f"[输入]: {text}")

    for name, prompt in steps:
        result = (prompt | llm | StrOutputParser()).invoke({"text": text})
        print(f"[{name}]: {result}")
