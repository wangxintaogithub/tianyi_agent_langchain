"""
RAG API - 检索增强生成（pgvector 语义检索）
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["RAG API"])

COLLECTION_TABLE = "langchain_knowledge"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# 示例知识库
INITIAL_KNOWLEDGE = [
    "LangChain 是一个用于构建 LLM 应用的框架，发布于 2022 年 10 月。",
    "LangChain 支持链式调用、Agent、记忆管理、RAG 等功能。",
    "LangChain 支持多种 LLM 提供商，包括 OpenAI、DeepSeek、Anthropic等。",
    "Agent 是 LangChain 中能够自主决策、调用工具的组件。",
    "RAG (Retrieval-Augmented Generation) 通过检索外部知识来增强 LLM 生成质量。",
    "LangChain Expression Language (LCEL) 是 LangChain 的声明式编程范式。",
]


def _get_vector_store():
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_postgres import PGVectorStore
    from utils.app.database import get_rag_engine, EMBEDDING_DIMENSION

    engine = get_rag_engine()
    engine.init_vectorstore_table(
        table_name=COLLECTION_TABLE,
        vector_size=EMBEDDING_DIMENSION,
    )
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return PGVectorStore.create_sync(
        engine=engine,
        table_name=COLLECTION_TABLE,
        embedding_service=embeddings,
    )


class RAGQueryRequest(BaseModel):
    query: str
    k: int = 3


class RAGQueryResponse(BaseModel):
    answer: str
    sources: list[str]


@router.post("/rag/query", response_model=RAGQueryResponse)
async def rag_query(req: RAGQueryRequest):
    """RAG 检索问答"""
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from utils.app.llm import get_deepseek_chat

        store = _get_vector_store()
        docs = store.similarity_search(req.query, k=req.k)

        if not docs:
            return RAGQueryResponse(answer="未找到相关文档。", sources=[])

        context = "\n\n".join([d.page_content for d in docs])
        llm = get_deepseek_chat()

        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个知识问答助手。请基于以下提供的上下文信息回答问题。"
                       "如果上下文不足以回答问题，请如实告知。\n\n上下文：\n{context}"),
            ("human", "{input}"),
        ])

        chain = prompt | llm | StrOutputParser()
        answer = chain.invoke({"context": context, "input": req.query})

        return RAGQueryResponse(
            answer=answer,
            sources=[d.page_content for d in docs],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/init")
async def rag_init():
    """初始化知识库（添加示例文档）"""
    try:
        from langchain_core.documents import Document

        store = _get_vector_store()
        existing = store.similarity_search("init check", k=1)
        if existing:
            return {"message": "知识库已就绪", "count": len(existing)}

        docs = [Document(page_content=text) for text in INITIAL_KNOWLEDGE]
        store.add_documents(docs)
        return {"message": f"知识库初始化完成", "count": len(docs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
