"""
CLI 主入口 - 运行所有示例
"""
from app.chains.basic_chain import run_basic_chain
from app.chains.conversation_chain import run_conversation_chain
from app.chains.multi_chain import run_sequential_chain, run_router_chain
from app.chains.memory_examples import run_buffer_memory, run_summary_memory, run_manual_history
from app.agents.agent_executor import run_simple_agent
from app.rag.rag_pipeline import run_rag_chain
from app.examples.translator import run_translator, run_text_processor

import os


def run_example(name, func):
    """运行单个示例并捕获异常"""
    print(f"\n{'='*50}")
    print(f"  运行: {name}")
    print(f"{'='*50}")
    try:
        func()
    except Exception as e:
        print(f"  ❌ 运行失败: {e}")


def run_all_examples(examples):
    """运行所有示例"""
    for _, name, func in examples:
        if func:
            run_example(name, func)


def run_selected_example(examples, choice):
    """运行指定编号的示例"""
    for key, name, func in examples:
        if key == choice and func:
            run_example(name, func)
            return True
    return False


def print_menu(examples):
    """打印菜单"""
    print("\n请选择要运行的示例:")
    for key, name, _ in examples:
        print(f"  [{key}] {name}")
    print("  [q] 退出")


def main():
    print("=" * 60)
    print("   LangChain 全套工程示例")
    print("   引擎: DeepSeek")
    print("=" * 60)

    if not os.getenv("DEEPSEEK_API_KEY"):
        print("\n⚠️  请先配置 .env 文件，设置 DEEPSEEK_API_KEY")
        print("   参考 backend/.env.example 文件\n")
        return

    examples = [
        ("1", "基础链 (Basic Chain)", run_basic_chain),
        ("2", "对话链 (Conversation Chain)", run_conversation_chain),
        ("3", "顺序链 (Sequential Chain)", run_sequential_chain),
        ("4", "路由链 (Router Chain)", run_router_chain),
        ("5", "记忆管理 (Memory Examples)", lambda: (
            run_buffer_memory(), run_summary_memory(), run_manual_history()
        )),
        ("6", "Agent 智能体", run_simple_agent),
        ("7", "RAG 检索增强生成", run_rag_chain),
        ("8", "翻译助手", run_translator),
        ("9", "文本处理管道", run_text_processor),
        ("0", "运行所有示例", None),
    ]

    print_menu(examples)
    choice = input("\n请输入编号: ").strip()

    if choice == "q":
        print("再见！")
    elif choice == "0":
        run_all_examples(examples)
    elif not run_selected_example(examples, choice):
        print("无效选择")


if __name__ == "__main__":
    main()
