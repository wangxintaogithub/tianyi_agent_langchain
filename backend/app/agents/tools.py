"""
自定义工具 - 供 Agent 使用
"""
from langchain_core.tools import tool
import datetime


@tool
def get_current_time() -> str:
    """获取当前日期和时间"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def calculate(expression: str) -> str:
    """执行数学计算，传入数学表达式如 '2 + 3 * 4'"""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"


@tool
def text_statistics(text: str) -> str:
    """统计文本的字符数、单词数、行数"""
    chars = len(text)
    words = len(text.split())
    lines = len(text.splitlines())
    return f"字符数: {chars}, 单词数: {words}, 行数: {lines}"


@tool
def reverse_text(text: str) -> str:
    """反转输入文本"""
    return text[::-1]


tools = [get_current_time, calculate, text_statistics, reverse_text]
