"""
多链组合 - 顺序链和路由链
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.models.llm import get_deepseek_chat


def run_sequential_chain():
    """顺序链 - 链式调用多个步骤"""
    llm = get_deepseek_chat()

    # 第一步: 头脑风暴
    brainstorm_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个创意顾问。针对用户的话题，列出 3 个有创意的点子，用数字列表。"),
        ("human", "话题：{topic}"),
    ])
    chain1 = brainstorm_prompt | llm | StrOutputParser()

    # 第二步: 评估
    evaluate_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是评论家。对以下创意进行点评，指出优缺点。"),
        ("human", "创意列表：\n{ideas}"),
    ])
    chain2 = evaluate_prompt | llm | StrOutputParser()

    # 第三步: 总结
    summary_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是总结专家。请用一句话总结以上讨论的核心要点。"),
        ("human", "讨论内容：\n{review}"),
    ])
    chain3 = summary_prompt | llm | StrOutputParser()

    print("\n=== 顺序链示例 ===")
    topic = "用 AI 改善城市交通"

    print(f"\n[话题]: {topic}")

    ideas = chain1.invoke({"topic": topic})
    print(f"\n[创意]:\n{ideas}")

    review = chain2.invoke({"ideas": ideas})
    print(f"\n[评价]:\n{review}")

    summary = chain3.invoke({"review": review})
    print(f"\n[总结]:\n{summary}")

    return {"ideas": ideas, "review": review, "summary": summary}


def run_router_chain():
    """路由链 - 根据输入路由到不同处理路径"""
    llm = get_deepseek_chat()

    # 路由判断 prompt
    router_prompt = ChatPromptTemplate.from_messages([
        ("system", "根据用户输入，只输出一个词：tech（科技）, life（生活）, edu（教育）, 或其他"),
        ("human", "{input}"),
    ])

    # 不同领域的 prompt
    prompts = {
        "tech": ChatPromptTemplate.from_messages([
            ("system", "你是一个科技专家，擅长解释技术概念。"),
            ("human", "{input}"),
        ]),
        "life": ChatPromptTemplate.from_messages([
            ("system", "你是一个生活顾问，擅长提供生活建议。"),
            ("human", "{input}"),
        ]),
        "edu": ChatPromptTemplate.from_messages([
            ("system", "你是一个教育专家，擅长解答学习问题。"),
            ("human", "{input}"),
        ]),
    }

    default_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个通用 AI 助手。"),
        ("human", "{input}"),
    ])

    print("\n=== 路由链示例 ===")
    inputs = [
        "Python 的装饰器是什么？",
        "如何提高学习效率？",
        "推荐几个北京的旅游景点",
    ]

    for inp in inputs:
        # 路由判断
        category = (router_prompt | llm | StrOutputParser()).invoke({"input": inp})
        category = category.strip().lower()

        prompt = prompts.get(category, default_prompt)
        result = (prompt | llm | StrOutputParser()).invoke({"input": inp})

        print(f"\n[用户]: {inp}")
        print(f"[路由 -> {category}]")
        print(f"[AI]: {result[:100]}...")
