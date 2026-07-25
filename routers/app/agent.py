"""
Agent API - Tool Calling Agent（langgraph 版）
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain.agents import create_agent
from langchain.agents.middleware import AgentState
from langgraph.prebuilt import ToolNode
from langgraph.graph.state import StateGraph, START, END
from langgraph.types import Command
from langchain_core.messages import AIMessage, HumanMessage
from utils.app.llm import get_deepseek_chat
from utils.app.tools import tools

router = APIRouter(prefix="/api", tags=["Agent API"])


class AgentRequest(BaseModel):
    prompt: str


class AgentResponse(BaseModel):
    reply: str


_executor = None

def _get_executor():
    global _executor
    if _executor is None:
        tool_node = ToolNode(tools)

        @create_agent
        def agent(state: AgentState) -> Command:
            llm = get_deepseek_chat().bind_tools(tools)
            response = llm.invoke(state["messages"])
            return Command(goto=END if not response.tool_calls else "tools", update={"messages": [response]})

        builder = StateGraph(AgentState)
        builder.add_node("agent", agent)
        builder.add_node("tools", tool_node)
        builder.add_edge(START, "agent")
        builder.add_conditional_edges("agent", lambda s: bool(s["messages"][-1].tool_calls), {True: "tools", False: END})
        builder.add_edge("tools", "agent")
        _executor = builder.compile()
    return _executor


@router.post("/agent", response_model=AgentResponse)
async def agent_chat(req: AgentRequest):
    """调用 Tool Calling Agent"""
    try:
        executor = _get_executor()
        result = await executor.ainvoke({"messages": [HumanMessage(content=req.prompt)]})
        last = result["messages"][-1]
        reply = last.content if isinstance(last, AIMessage) else str(last.content)
        return AgentResponse(reply=reply or "处理完成")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
