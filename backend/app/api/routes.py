"""
API 路由定义
"""
import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

router = APIRouter()

# === 系统内置 Prompt ===
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


class ConversationRequest(BaseModel):
    prompt: str
    session_id: str = "default"
    temperature: float | None = None
    max_tokens: int | None = None


class ConversationResponse(BaseModel):
    reply: str
    model: str
    session_id: str


# === API 端点 ===

@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """调用 LLM（无状态，支持自定义系统提示词）"""
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from app.models.llm import get_deepseek_chat

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


@router.post("/conversation", response_model=ConversationResponse)
async def conversation(req: ConversationRequest):
    """带 PostgreSQL 持久化对话历史的聊天接口"""
    try:
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        from langchain_core.output_parsers import StrOutputParser
        from langchain_postgres import PostgresChatMessageHistory
        from langchain_core.runnables.history import RunnableWithMessageHistory
        from app.database import get_sync_connection
        from app.models.llm import get_deepseek_chat

        llm = get_deepseek_chat(
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )

        # 初始化 PostgreSQL 连接和表
        CHAT_HISTORY_TABLE = "chat_histories"
        conn = get_sync_connection()
        PostgresChatMessageHistory.create_tables(conn, CHAT_HISTORY_TABLE)

        def get_session_history(session_id: str) -> PostgresChatMessageHistory:
            return PostgresChatMessageHistory(
                CHAT_HISTORY_TABLE, session_id, sync_connection=conn,
            )

        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
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

        reply = chain_with_history.invoke(
            {"input": req.prompt},
            config={"configurable": {"session_id": req.session_id}},
        )

        return ConversationResponse(
            reply=reply,
            model="deepseek",
            session_id=req.session_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 文件上传 & 处理 API
# ============================================================

ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx",
    ".xls", ".xlsx", ".csv",
    ".txt", ".md", ".json", ".xml", ".yaml", ".yml", ".log",
    ".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".go", ".rs", ".sh", ".bat",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 单个文件 50MB
MAX_FILES = 20                     # 单次最多 20 个文件


@router.post("/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    wechat_webhook: str | None = Form(None),
    send_to_wechat: bool = Form(True),
    upload_to_cos: bool = Form(True),
):
    """上传并处理多个文件

    - 解析文件内容（PDF/DOCX/Excel/CSV/文本）
    - 可选上传到腾讯云 COS
    - 可选发送处理报告到企业微信群

    Args:
        files: 多个文件（multipart/form-data）
        wechat_webhook: 可选，覆盖默认的企业微信 Webhook 地址
        send_to_wechat: 是否发送处理报告到微信群（默认 true）
        upload_to_cos: 是否上传文件到腾讯云 COS（默认 true）
    """
    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"单次最多上传 {MAX_FILES} 个文件",
        )

    results = []
    breakpoint()

    for file in files:
        filename = file.filename or "unknown"
        ext = os.path.splitext(filename)[1].lower()

        # 检查扩展名
        if ext not in ALLOWED_EXTENSIONS:
            results.append({
                "filename": filename,
                "status": "skipped",
                "reason": f"不支持的文件类型: {ext}",
            })
            continue

        # 读取文件内容（限制大小）
        raw = await file.read()
        if len(raw) > MAX_FILE_SIZE:
            results.append({
                "filename": filename,
                "status": "skipped",
                "reason": "文件超过大小限制 (50MB)",
            })
            continue

        import io
        from app.services.file_parser import parse_file
        from app.services.cos_uploader import upload_file as cos_upload

        file_bytes = io.BytesIO(raw)

        # 1. 解析文件内容
        content = parse_file(file_bytes, filename)

        result: dict = {
            "filename": filename,
            "ext": ext,
            "size": len(raw),
            "status": "ok",
            "content_preview": content[:500],
            "content_length": len(content),
        }

        # 2. 上传到腾讯云 COS
        cos_result = None
        if upload_to_cos:
            file_bytes.seek(0)
            cos_result = cos_upload(file_bytes, filename)
            if cos_result["status"] == "ok":
                result["cos_url"] = cos_result["cos_url"]
                result["cos_key"] = cos_result["cos_key"]
            else:
                result["cos_status"] = "failed"
                result["cos_error"] = cos_result.get("error")

        results.append(result)

    # 3. 发送处理报告到企业微信群
    if send_to_wechat:
        try:
            from app.services.wechat_bot import send_file_result_summary
            wechat_resp = send_file_result_summary(results, webhook_url=wechat_webhook)
        except Exception as e:
            wechat_resp = {"errcode": -1, "errmsg": str(e)}
    else:
        wechat_resp = None

    # 汇总
    success_count = sum(1 for r in results if r["status"] == "ok")
    skip_count = sum(1 for r in results if r["status"] == "skipped")

    return {
        "total": len(results),
        "success": success_count,
        "skipped": skip_count,
        "results": results,
        "wechat_notify": wechat_resp,
    }
