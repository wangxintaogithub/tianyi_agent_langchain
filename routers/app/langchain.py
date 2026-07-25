"""
LangChain API 路由 - AI 对话 + Agent + RAG
通过 `/api/` 前缀对外提供 RESTful API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.app.llm import get_deepseek_chat

router = APIRouter(prefix="/api", tags=["LangChain API"])

SYSTEM_PROMPT = "你是一个智能助手。请用中文回答，回答简洁准确。"


# === 请求/响应模型 ===

class ChatRequest(BaseModel):
    prompt: str
    system_prompt: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


class ChatResponse(BaseModel):
    reply: str
    model: str


# === 健康检查 ===

@router.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}


# === 聊天 API ===

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """调用 LLM 对话（无状态）"""
    try:
        from langchain_core.prompts import ChatPromptTemplate
        llm = get_deepseek_chat(
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
        system_prompt = req.system_prompt or SYSTEM_PROMPT
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        chain = prompt | llm
        reply = chain.invoke({"input": req.prompt}).content
        return ChatResponse(reply=reply, model="deepseek")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === 带历史记录的对话 API ===

class ConversationRequest(BaseModel):
    prompt: str
    session_id: str = "default"
    temperature: float | None = None
    max_tokens: int | None = None


class ConversationResponse(BaseModel):
    reply: str
    model: str
    session_id: str


@router.post("/conversation", response_model=ConversationResponse)
async def conversation(req: ConversationRequest):
    """带 PostgreSQL 持久化对话历史的聊天"""
    try:
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        from langchain_core.output_parsers import StrOutputParser
        from langchain_postgres import PostgresChatMessageHistory
        from langchain_core.runnables.history import RunnableWithMessageHistory
        from utils.core.db import get_engine
        from sqlmodel import Session

        llm = get_deepseek_chat(
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )

        engine = get_engine()
        with Session(engine) as conn:
            CHAT_HISTORY_TABLE = "chat_histories"
            PostgresChatMessageHistory.create_tables(conn.connection(), CHAT_HISTORY_TABLE)

            def get_session_history(session_id: str) -> PostgresChatMessageHistory:
                return PostgresChatMessageHistory(
                    CHAT_HISTORY_TABLE, session_id, sync_connection=conn.connection(),
                )

            prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ])

            chain = prompt | llm | StrOutputParser()
            chain_with_history = RunnableWithMessageHistory(
                chain, get_session_history,
                input_messages_key="input", history_messages_key="history",
            )

            reply = chain_with_history.invoke(
                {"input": req.prompt},
                config={"configurable": {"session_id": req.session_id}},
            )

            return ConversationResponse(reply=reply, model="deepseek", session_id=req.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
