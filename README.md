# Azure Doc Agent - Skills & MCP

一个基于 Microsoft Agent Framework 的智能文档助手，集成了 Agent Skills 和 MCP（Model Context Protocol）。

## 🌟 核心特性

### 🎯 渐进式披露架构

**关键设计1：所有MCP工具在初始化时注册，SKILL.md指导Agent何时使用它们**

- 所有MCP Server的工具在Agent初始化时一次性注册
- SKILL.md通过文字说明告诉Agent在什么情况下使用哪些工具
- 不同Skill可以指导使用不同MCP Server的工具
- 完美支持多MCP Server扩展，易于添加新的Skills和MCP集成

**关键设计2：LLM智能Skill匹配（无需硬编码关键词）**

- 使用LLM理解用户意图，智能匹配最相关的Skill
- 支持任何语言（中文、英文、混合等）、任何表达方式
- 无需为每个Skill维护关键词列表
- 关键词匹配作为fallback确保稳定性

📖 详细架构说明: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)  

### 其他特性

- **🎨 Modern Web UI**: React + TypeScript + Vite 前端界面（Dark主题 + SSE流式响应）
- **🤖 Agent Skills 集成**: 基于 [agentskills.io](https://agentskills.io) 标准的技能发现和动态注入
- **🔌 MCP 客户端**: 连接 Microsoft Learn MCP Server，访问官方文档
- **💬 多轮对话**: 支持线程管理和对话上下文维护
- **🧠 短期记忆**: In-memory 对话历史保留
- **⚡ 异步架构**: 使用 asyncio 实现高性能并发
- **📡 REST API**: FastAPI 后端服务
- **💭 Thinking显示**: 实时展示Agent的思考过程（Skill匹配、激活、工具选择）

## 📁 项目结构

```
AzureDoc_Skills_MCP/
├── src/                          # 源代码目录
│   ├── azure_doc_agent.py       # 主 Agent 类（渐进式披露逻辑）
│   ├── api_server.py            # FastAPI 后端服务器
│   ├── registry.py              # 技能注册表（智能匹配 min_score=50）
│   ├── injector.py              # 技能注入器（按需加载完整SKILL.md）
│   ├── mcp_client.py            # MCP 客户端（多MCP Server支持）
│   └── system_prompts.py        # 系统提示管理
├── frontend/                     # React 前端
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── styles/
│   │   ├── types/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── skills/                       # 技能定义目录
│   ├── microsoft-docs/          # 文档搜索技能
│   │   └── SKILL.md            # 指导使用 microsoft_docs_search/fetch
│   └── microsoft-code-reference/ # 代码参考技能
│       └── SKILL.md            # 指导使用 microsoft_code_sample_search
├── docs/                         # 文档目录 (新)
│   ├── ARCHITECTURE.md          # 完整架构说明
│   └── QUICK_REFERENCE.md       # 快速参考
├── logs/                         # 日志文件目录
├── main.py                       # CLI 程序入口
├── start.sh                      # 启动脚本
├── test_correct_logic.py         # 渐进式披露逻辑测试
├── test_skill_guidance.py        # SKILL指导测试
├── requirements.txt              # Python 依赖
├── .env.example                  # 环境变量示例
└── README.md                     # 项目文档
```

## 🏗️ 架构亮点

### 渐进式披露的三个层面

1. **Skill层面**: metadata常驻内存，完整内容匹配后按需加载
2. **工具层面**: 所有MCP工具预先注册，SKILL.md指导何时使用
3. **扩展层面**: 多MCP Server共存，不同Skill指导不同工具

### 查询处理流程

```
用户查询 → Skill匹配 (min_score=50)
         ↓
         匹配成功? → 加载完整SKILL.md → 注入Agent Context
         ↓                                ↓
         匹配失败  →  通用对话            Agent根据SKILL.md指导选择工具
```

**示例：**
- "Azure Functions文档" → 匹配microsoft-docs → Agent使用microsoft_docs_search
- "Python代码示例" → 匹配microsoft-code-reference → Agent使用microsoft_code_sample_search
- "hello world" → 无匹配 → 通用对话（不使用MCP工具）

## 🚀 快速开始

### 方式 1: Web UI（推荐）

```bash
# 1. 安装 Python 依赖
pip install -r requirements.txt

# 2. 安装前端依赖
./setup-frontend.sh

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填写 Azure OpenAI 配置

# 4. 启动服务器（后端 + 前端）
./start.sh
```

访问:
- **Web UI**: http://localhost:3000
- **API文档**: http://localhost:8000/docs

### 方式 2: CLI 模式

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境
cp .env.example .env

# 3. 运行 CLI
python main.py
```

## 💡 使用示例

### 基本对话

```python
from src.azure_doc_agent import AzureDocAgent
import asyncio

async def main():
    # 初始化 Agent
    agent = AzureDocAgent(
        azure_openai_endpoint="https://your-resource.openai.azure.com/",
        azure_openai_key="your-key",
        azure_openai_deployment="gpt-4o"
    )
    
    await agent.initialize()
    
    # 创建对话线程
    thread_id = agent.create_thread()
    
    # 发送消息
    response = await agent.chat(
        "我需要了解 Azure Functions 的端到端教程"
    )
    
    print(response)
    
    await agent.close()

asyncio.run(main())
```

### 多线程对话

```python
# 创建多个对话线程
thread1 = agent.create_thread("azure-functions")
thread2 = agent.create_thread("cosmos-db")

# 在不同线程中对话
await agent.chat("Azure Functions 概述", thread_id=thread1)
await agent.chat("Cosmos DB 分区策略", thread_id=thread2)

# 切换线程
agent.switch_thread(thread1)
await agent.chat("如何部署 Azure Functions？")
```

## 🎯 核心组件

### 1. Skill Registry（技能注册表）

自动发现和索引 `skills/` 目录下的所有技能：

```python
registry = SkillRegistry("skills")
skill_count = registry.discover_skills()
skills = registry.list_skills()
```

### 2. Skill Injector（技能注入器）

动态激活技能并注入到对话上下文：

```python
injector = SkillInjector(registry)
content = injector.activate_skill("microsoft-docs")
```

### 3. MCP Client（MCP 客户端）

连接 Microsoft Learn MCP Server：

```python
mcp_client = MCPClient("https://learn.microsoft.com/api/mcp")
await mcp_client.initialize()

# 搜索文档
results = await mcp_client.search_docs("Azure Functions", max_results=5)

# 获取完整文档
content = await mcp_client.fetch_doc("https://learn.microsoft.com/...")
```

### 4. System Prompts Manager（系统提示管理器）

动态生成系统提示：

```python
prompts_manager = SystemPromptsManager(registry, injector)
system_prompt = prompts_manager.build_full_system_prompt()
```

## 🔧 技能系统

### 技能定义格式

每个技能包含一个 `SKILL.md` 文件，使用 YAML front matter 定义元数据：

```markdown
---
name: microsoft-docs
description: Query official Microsoft documentation
context: fork
compatibility: Requires Microsoft Learn MCP Server
tags: ["documentation", "microsoft", "azure"]
---

# Microsoft Docs

## Tools
...
```

### 添加新技能

1. 在 `skills/` 下创建新目录
2. 添加 `SKILL.md` 文件
3. Agent 启动时自动发现

## 📊 工作流程

```
用户查询
    ↓
Skill Registry 搜索相关技能
    ↓
Skill Injector 激活技能
    ↓
动态更新系统提示
    ↓
LLM 决定使用的工具
    ↓
调用 MCP 或激活更多技能
    ↓
返回结果给用户
```

## 🔍 日志

所有日志输出到 `logs/agent.log`：

```bash
tail -f logs/agent.log
```

## 🛠️ 开发

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black src/
flake8 src/
mypy src/
```

## 📝 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI / AI Foundry 端点 | - |
| `AZURE_OPENAI_KEY` | API 密钥 | - |
| `AZURE_OPENAI_DEPLOYMENT` | 模型部署名称 | gpt-4o |
| `MCP_SERVERS` | MCP 服务器列表（逗号分隔） | ms-learn |
| `SKILLS_DIRECTORY` | 技能目录 | skills |
| `LOG_LEVEL` | 日志级别 | INFO |
| `MAX_HISTORY_LENGTH` | 最大历史消息数 | 20 |

> 💡 **AI Foundry 用户**: 使用 AI Foundry 中的模型时，`AZURE_OPENAI_ENDPOINT` 填写您的 AI Foundry 项目端点，格式相同。


## 🔗 相关链接

- [Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/)
- [Agent Skills Standard](https://agentskills.io)
- [Microsoft Learn MCP Server](https://github.com/MicrosoftDocs/mcp/tree/main)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [Skills](https://github.com/MicrosoftDocs/mcp/blob/main/skills/microsoft-docs/SKILL.md)
          (https://github.com/MicrosoftDocs/mcp/blob/main/skills/microsoft-code-reference/SKILL.md)
          
## 📞 支持

如有问题，请提交 Issue 或联系维护者。
