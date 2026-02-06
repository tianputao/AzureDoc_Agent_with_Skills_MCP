"""
Main Entry Point - Azure Doc Agent 主程序

启动交互式命令行界面
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv
from colorlog import ColoredFormatter

from src.azure_doc_agent import AzureDocAgent


def setup_logging(log_level: str = "INFO", log_file: str = "logs/agent.log") -> None:
    """
    配置日志系统（按日期分割）
    
    Args:
        log_level: 日志级别
        log_file: 日志文件路径
    """
    # 确保日志目录存在
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 配置颜色格式化器（用于控制台）
    console_formatter = ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    # 配置文件格式化器
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器 - 按日期分割
    # 使用TimedRotatingFileHandler，每天午夜创建新文件
    file_handler = TimedRotatingFileHandler(
        log_file,
        when='midnight',
        interval=1,
        backupCount=30,  # 保留30天的日志
        encoding='utf-8'
    )
    file_handler.suffix = "%Y-%m-%d"  # 日志文件名后缀格式
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    logging.info("日志系统已初始化（按日期分割）")


def load_config() -> dict:
    """
    加载配置
    
    Returns:
        配置字典
    """
    # 加载 .env 文件
    load_dotenv()
    
    config = {
        "azure_openai_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "azure_openai_key": os.getenv("AZURE_OPENAI_KEY"),
        "azure_openai_deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        "mcp_server_url": os.getenv("MCP_SERVER_URL", "https://learn.microsoft.com/api/mcp"),
        "skills_directory": os.getenv("SKILLS_DIRECTORY", "skills"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "log_file": os.getenv("LOG_FILE", "logs/agent.log"),
        "max_history_length": int(os.getenv("MAX_HISTORY_LENGTH", "20")),
    }
    
    # 验证必需配置
    if not config["azure_openai_endpoint"]:
        raise ValueError("AZURE_OPENAI_ENDPOINT 未配置")
    if not config["azure_openai_key"]:
        raise ValueError("AZURE_OPENAI_KEY 未配置")
    
    return config


def print_welcome():
    """打印欢迎信息"""
    welcome_text = """
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║          Azure Doc Agent - Skills & MCP                    ║
║                                                            ║
║   智能文档助手 - 支持多轮对话和技能动态注入                  ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝

可用命令:
  /help     - 显示帮助信息
  /skills   - 列出可用技能
  /threads  - 列出所有对话线程
  /new      - 创建新对话线程
  /switch   - 切换对话线程
  /history  - 显示当前线程历史
  /clear    - 清空对话历史
  /exit     - 退出程序

开始对话，输入您的问题...
"""
    print(welcome_text)


async def interactive_mode(agent: AzureDocAgent) -> None:
    """
    交互式命令行模式
    
    Args:
        agent: Agent 实例
    """
    print_welcome()
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\n您: ").strip()
            
            if not user_input:
                continue
            
            # 处理命令
            if user_input.startswith('/'):
                await handle_command(agent, user_input)
                continue
            
            # 处理普通消息
            print("\nAgent: ", end="", flush=True)
            response = await agent.chat(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except EOFError:
            print("\n\n再见！")
            break
        except Exception as e:
            logging.error(f"处理用户输入时出错: {e}")
            print(f"\n❌ 错误: {e}")


async def handle_command(agent: AzureDocAgent, command: str) -> None:
    """
    处理命令
    
    Args:
        agent: Agent 实例
        command: 命令字符串
    """
    cmd = command.lower().split()[0]
    
    if cmd == "/help":
        print_help()
    
    elif cmd == "/skills":
        skills = agent.registry.list_skills()
        print("\n可用技能:")
        for skill in skills:
            print(f"\n  📚 {skill.name}")
            print(f"     {skill.description}")
            print(f"     标签: {', '.join(skill.tags)}")
    
    elif cmd == "/threads":
        threads = list(agent.threads.keys())
        current = agent.current_thread_id
        print("\n对话线程:")
        for thread_id in threads:
            marker = "→" if thread_id == current else " "
            msg_count = len(agent.threads[thread_id])
            print(f"  {marker} {thread_id} ({msg_count} 条消息)")
    
    elif cmd == "/new":
        parts = command.split(maxsplit=1)
        thread_id = parts[1] if len(parts) > 1 else None
        new_thread = agent.create_thread(thread_id)
        print(f"\n✅ 已创建新线程: {new_thread}")
    
    elif cmd == "/switch":
        parts = command.split(maxsplit=1)
        if len(parts) < 2:
            print("\n❌ 请指定线程 ID")
            return
        thread_id = parts[1]
        if agent.switch_thread(thread_id):
            print(f"\n✅ 已切换到线程: {thread_id}")
        else:
            print(f"\n❌ 线程不存在: {thread_id}")
    
    elif cmd == "/history":
        history = agent.get_thread_history()
        print(f"\n当前线程历史 ({agent.current_thread_id}):")
        for i, entry in enumerate(history, 1):
            print(f"\n[{i}] {entry['timestamp']}")
            print(f"  用户: {entry['user']}")
            print(f"  助手: {entry['assistant'][:100]}...")
    
    elif cmd == "/clear":
        agent.clear_history()
        print("\n✅ 已清空对话历史")
    
    elif cmd == "/exit":
        print("\n再见！")
        await agent.close()
        sys.exit(0)
    
    else:
        print(f"\n❌ 未知命令: {cmd}")
        print("输入 /help 查看可用命令")


def print_help():
    """打印帮助信息"""
    help_text = """
命令列表:

  /help              显示此帮助信息
  /skills            列出所有可用技能及其描述
  /threads           列出所有对话线程
  /new [thread_id]   创建新对话线程（可选指定 ID）
  /switch <thread_id>切换到指定线程
  /history           显示当前线程的对话历史
  /clear             清空当前对话历史
  /exit              退出程序

使用示例:
  
  查询文档:
    我需要了解 Azure Functions 的概述
    
  激活技能:
    (自动根据查询激活相关技能)
    
  多线程对话:
    /new azure-functions
    /switch azure-functions
    如何部署 Azure Functions？
"""
    print(help_text)


async def main():
    """主函数"""
    try:
        # 加载配置
        config = load_config()
        
        # 配置日志
        setup_logging(config["log_level"], config["log_file"])
        
        logging.info("启动 Azure Doc Agent...")
        
        # 初始化 Agent
        agent = AzureDocAgent(
            azure_openai_endpoint=config["azure_openai_endpoint"],
            azure_openai_key=config["azure_openai_key"],
            azure_openai_deployment=config["azure_openai_deployment"],
            mcp_server_url=config["mcp_server_url"],
            skills_directory=config["skills_directory"]
        )
        
        # 初始化
        success = await agent.initialize()
        if not success:
            logging.error("Agent 初始化失败")
            return
        
        # 创建默认线程
        agent.create_thread("default")
        
        # 启动交互模式
        await interactive_mode(agent)
        
        # 关闭
        await agent.close()
        
    except ValueError as e:
        logging.error(f"配置错误: {e}")
        print(f"\n❌ 配置错误: {e}")
        print("请检查 .env 文件是否正确配置")
        sys.exit(1)
    except Exception as e:
        logging.error(f"启动失败: {e}", exc_info=True)
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 运行主程序
    asyncio.run(main())
