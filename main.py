"""
主入口 - 运行所有示例（兼容旧路径）

运行方式：
  python main.py                  # 从项目根目录运行
  python -m backend.app.cli       # 从项目根目录（新路径）
  cd backend && python -m app.cli # 从 backend 目录
"""
import sys
import os

# 将 backend 目录加入 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.chains.basic_chain import run_basic_chain
from app.chains.conversation_chain import run_conversation_chain
from app.chains.multi_chain import run_sequential_chain, run_router_chain
from app.chains.memory_examples import run_buffer_memory, run_summary_memory, run_manual_history
from app.agents.agent_executor import run_simple_agent
from app.rag.rag_pipeline import run_rag_chain
from app.examples.translator import run_translator, run_text_processor


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

    print("\n请选择要运行的示例:")
    for key, name, _ in examples:
        print(f"  [{key}] {name}")
    print("  [q] 退出")

    choice = input("\n请输入编号: ").strip()

    if choice == "q":
        print("再见！")
        return
    elif choice == "0":
        for _, name, func in examples:
            if func:
                print(f"\n{'='*50}")
                print(f"  运行: {name}")
                print(f"{'='*50}")
                try:
                    func()
                except Exception as e:
                    print(f"  ❌ 运行失败: {e}")
    else:
        for key, name, func in examples:
            if key == choice and func:
                print(f"\n{'='*50}")
                print(f"  运行: {name}")
                print(f"{'='*50}")
                try:
                    func()
                except Exception as e:
                    print(f"  ❌ 运行失败: {e}")
                break
        else:
            print("无效选择")


if __name__ == "__main__":
    main()
