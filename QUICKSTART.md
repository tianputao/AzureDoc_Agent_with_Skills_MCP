# 快速开始指南

## 🚀 5 分钟上手

### 步骤 1: 克隆或下载项目

项目已在当前目录准备就绪：`/home/tarhone/AzureDoc_Skills_MCP`

### 步骤 2: 安装依赖

```bash
# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 步骤 3: 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env 文件
nano .env  # 或使用你喜欢的编辑器
```

填写以下必需配置：
```env
# 使用 Azure OpenAI 或 AI Foundry 的端点
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# 或 AI Foundry: https://your-project.api.azureml.ms/
AZURE_OPENAI_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

### 步骤 4: 测试基础功能

```bash
# 运行基础测试（不需要 Azure OpenAI）
python test_basic.py
```

预期输出：
```
============================================================
Azure Doc Agent - 功能测试
============================================================
测试 Skill Registry
============================================================

✅ 发现 2 个技能

📚 microsoft-docs
   描述: Query official Microsoft documentation...
   标签: documentation, microsoft, azure, learning
   ...
```

### 步骤 5: 启动 Agent

```bash
python main.py
```

成功启动后会看到：
```
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
  ...

您: 
```

## 💡 第一次对话

### 示例 1: 查询文档

```
您: 我需要了解 Azure Functions 的概述

Agent: 让我为您搜索 Azure Functions 的官方文档...

[自动激活技能: microsoft-docs]
[调用 MCP: search_microsoft_docs]

根据 Microsoft Learn 的文档，Azure Functions 是...
```

### 示例 2: 多轮对话

```
您: 什么是 Azure Functions？

Agent: Azure Functions 是 Azure 提供的无服务器计算服务...

您: 它支持哪些编程语言？

Agent: Azure Functions 支持以下编程语言：
- C#
- JavaScript/TypeScript
- Python
- Java
- PowerShell
...

您: 给我一个 Python 示例

Agent: 这里是一个简单的 Python Azure Function 示例...
```

## 🎯 常用命令

### 技能管理

```bash
# 列出所有技能
您: /skills

# 输出：
可用技能:

  📚 microsoft-docs
     Query official Microsoft documentation...
     标签: documentation, microsoft, azure, learning

  📚 microsoft-code-reference
     Access Microsoft code samples, API references...
     标签: code, api, sdk, reference, samples
```

### 线程管理

```bash
# 创建新线程
您: /new azure-learning

# 切换线程
您: /switch azure-learning

# 查看所有线程
您: /threads
```

### 历史管理

```bash
# 查看历史
您: /history

# 清空历史
您: /clear
```

## 🔧 故障排查

### 问题 1: 找不到模块

**错误信息**:
```
ModuleNotFoundError: No module named 'openai'
```

**解决方案**:
```bash
pip install -r requirements.txt
```

### 问题 2: Azure OpenAI 认证失败

**错误信息**:
```
❌ 配置错误: AZURE_OPENAI_ENDPOINT 未配置
```

**解决方案**:
1. 检查 `.env` 文件是否存在
2. 确认配置项正确填写
3. 验证 API key 是否有效

### 问题 3: MCP 连接失败

**错误信息**:
```
MCP 服务器初始化失败
```

**解决方案**:
1. 检查网络连接
2. 验证 MCP_SERVER_URL 配置
3. 查看日志: `tail -f logs/agent.log`

### 问题 4: 技能未发现

**错误信息**:
```
发现 0 个技能
```

**解决方案**:
1. 确认 `.skills/` 目录存在
2. 检查 SKILL.md 文件格式
3. 验证 SKILLS_DIRECTORY 配置

## 📊 验证安装

运行完整验证：

```bash
# 1. 测试技能系统
python test_basic.py

# 2. 检查依赖
pip list | grep -E "openai|httpx|azure"

# 3. 验证配置
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✅ 配置加载成功' if os.getenv('AZURE_OPENAI_ENDPOINT') else '❌ 配置缺失')"

# 4. 测试日志系统
mkdir -p logs && echo "测试日志" > logs/test.log && cat logs/test.log
```

## 🎓 学习路径

### 初级（5-10 分钟）
1. ✅ 完成快速开始
2. ✅ 尝试基本查询
3. ✅ 了解命令系统

### 中级（20-30 分钟）
1. 📖 阅读 [README.md](README.md)
2. 🔍 探索多轮对话
3. 🧵 使用线程管理
4. 📚 查看 [docs/BLOG_POST_CN.md](docs/BLOG_POST_CN.md)

### 高级（1-2 小时）
1. 🏗️ 阅读 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
2. 🔧 添加自定义技能
3. 🚀 部署到 Azure（参考 [DEPLOYMENT.md](DEPLOYMENT.md)）
4. 💻 集成到自己的应用

## 📝 下一步

### 自定义技能

创建新技能 `skills/my-skill/SKILL.md`:

```markdown
---
name: my-skill
description: 我的自定义技能
context: fork
compatibility: 兼容说明
tags: ["custom", "example"]
---

# My Skill

## Tools
...
```

重启 Agent 后自动发现新技能。

### 集成到应用

```python
from src.azure_doc_agent import AzureDocAgent
import asyncio

async def my_app():
    agent = AzureDocAgent(
        azure_openai_endpoint="...",
        azure_openai_key="...",
        azure_openai_deployment="gpt-4o"
    )
    
    await agent.initialize()
    response = await agent.chat("查询文档")
    print(response)
    await agent.close()

asyncio.run(my_app())
```

### 部署到生产

参考 [DEPLOYMENT.md](DEPLOYMENT.md) 了解：
- Azure 部署
- Docker 容器化
- 性能优化
- 监控配置

## 🆘 获取帮助

### 文档
- [README.md](README.md) - 项目概述
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - 项目结构
- [docs/BLOG_POST_CN.md](docs/BLOG_POST_CN.md) - 架构设计
- [DEPLOYMENT.md](DEPLOYMENT.md) - 部署指南

### 日志
```bash
# 实时日志
tail -f logs/agent.log

# 调试模式
export LOG_LEVEL=DEBUG
python main.py
```

### 社区
- 提交 Issue
- 查看示例代码
- 阅读文档

## ✨ 提示和技巧

### 1. 更好的查询
❌ 不好: "Azure"
✅ 好: "Azure Functions Python v2 programming model quickstart"

### 2. 利用上下文
在多轮对话中，Agent 会记住之前的对话，可以直接追问。

### 3. 使用线程
为不同主题创建不同线程，保持对话聚焦。

### 4. 查看技能
使用 `/skills` 了解 Agent 的能力范围。

### 5. 保存重要对话
使用 `/history` 查看和保存对话历史。

## 🎉 完成！

现在你已经成功运行了 Azure Doc Agent！

开始探索 Microsoft 文档的强大功能吧！ 🚀
