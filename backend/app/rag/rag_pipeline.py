"""
RAG (检索增强生成) 管道 - pgvector 语义检索

使用 langchain-postgres v0.0.14+ 的 PGVectorStore 替代旧版 PGVector，
通过向量相似度检索替代关键词匹配，大幅提升检索质量。

前置条件：
1. PostgreSQL 16+ 已安装并运行
2. pgvector 扩展已启用（`CREATE EXTENSION vector;`）
3. 数据库已创建（默认: langchain_db）
"""
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVectorStore
from app.models.llm import get_deepseek_chat
from app.config import settings
from app.database import get_engine, EMBEDDING_DIMENSION


# 示例知识库
SAMPLE_KNOWLEDGE = [
    "LangChain 是一个用于构建 LLM 应用的框架，发布于 2022 年 10 月。",
    "LangChain 支持链式调用、Agent、记忆管理、RAG 等功能。",
    "LangChain 支持多种 LLM 提供商，包括 OpenAI、DeepSeek、Anthropic等。",
    "Agent 是 LangChain 中能够自主决策、调用工具的组件。",
    "RAG (Retrieval-Augmented Generation) 通过检索外部知识来增强 LLM 生成质量。",
    "LangChain Expression Language (LCEL) 是 LangChain 的声明式编程范式。",
]

COLLECTION_TABLE = "langchain_knowledge"

# 全局缓存的嵌入模型实例
_embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)


def get_vector_store() -> PGVectorStore:
    """获取或创建向量存储"""
    engine = get_engine()

    # 建表（仅表不存在时创建）
    engine.init_vectorstore_table(
        table_name=COLLECTION_TABLE,
        vector_size=EMBEDDING_DIMENSION,
    )

    store = PGVectorStore.create_sync(
        engine=engine,
        table_name=COLLECTION_TABLE,
        embedding_service=_embeddings,
    )
    return store


def initialize_knowledge_base() -> str:
    """初始化知识库（如为空则添加示例文档）"""
    store = get_vector_store()

    # 检查是否已有文档
    existing = store.similarity_search("init check", k=1)
    if existing:
        return f"知识库已就绪（{len(existing)} 条文档）"

    # 添加示例文档
    docs = [Document(page_content=text) for text in SAMPLE_KNOWLEDGE]
    store.add_documents(docs)
    return f"知识库初始化完成，已添加 {len(docs)} 条文档"


def retrieve_docs(query: str, k: int = 3) -> str:
    """使用向量语义相似度检索文档"""
    store = get_vector_store()
    results = store.similarity_search(query, k=k)
    if not results:
        return "未找到相关文档。"
    return "\n\n".join([doc.page_content for doc in results])


def create_rag_chain():
    """创建 RAG 链"""
    llm = get_deepseek_chat()

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个知识问答助手。请基于以下提供的上下文信息回答问题。"
                   "如果上下文不足以回答问题，请如实告知。\n\n上下文：\n{context}"),
        ("human", "{input}"),
    ])

    def format_context(input_dict: dict) -> dict:
        context = retrieve_docs(input_dict["input"])
        return {"context": context, "input": input_dict["input"]}

    chain = (
        RunnablePassthrough() | format_context | prompt | llm | StrOutputParser()
    )
    return chain


def run_rag_chain():
    """运行 RAG 示例"""
    print("\n=== RAG 检索增强生成 ===")
    print(initialize_knowledge_base())

    chain = create_rag_chain()
    questions = [
        "LangChain 是什么？",
        "什么是 RAG？",
    ]
    for q in questions:
        print(f"\n[用户]: {q}")
        result = chain.invoke({"input": q})
        print(f"[AI]: {result}")
