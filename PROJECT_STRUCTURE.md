# 项目结构总览

## 完整文件树

```
AzureDoc_Skills_MCP/
│
├── 📁 src/                           # 源代码目录
│   ├── __init__.py                   # 包初始化文件
│   ├── azure_doc_agent.py            # 主 Agent 类（核心）
│   ├── registry.py                   # 技能注册表
│   ├── injector.py                   # 技能注入器
│   ├── mcp_client.py                 # MCP 客户端
│   └── system_prompts.py             # 系统提示管理器
│
├── 📁 .skills/                       # 技能定义目录
│   ├── 📁 microsoft-docs/            # 文档搜索技能
│   │   └── SKILL.md                  # 技能定义文件
│   └── 📁 microsoft-code-reference/  # 代码参考技能
│       └── SKILL.md                  # 技能定义文件
│
├── 📁 logs/                          # 日志文件目录（运行时生成）
│   └── agent.log                     # 应用日志
│
├── 📄 main.py                        # 程序主入口（CLI）
├── 📄 test_basic.py                  # 基础功能测试脚本
│
├── 📄 requirements.txt               # Python 依赖包列表
├── 📄 .env.example                   # 环境变量示例
├── 📄 .gitignore                     # Git 忽略文件
│
├── 📄 README.md                      # 项目说明文档
├── 📄 DEPLOYMENT.md                  # 部署指南
├── 📄 EXAMPLES.md                    # 使用示例
└── 📄 PROJECT_STRUCTURE.md           # 本文件（项目结构说明）
```

## 核心组件说明

### 1. src/azure_doc_agent.py（主 Agent）
**职责**: 
- 整合所有组件
- 管理对话线程
- 处理用户消息
- 调用 LLM 和工具
- 维护对话历史

**关键类**: `AzureDocAgent`

**关键方法**:
- `initialize()` - 初始化 Agent
- `chat()` - 处理用户消息
- `create_thread()` - 创建对话线程
- `_call_llm()` - 调用 LLM
- `_handle_tool_calls()` - 处理工具调用

### 2. src/registry.py（技能注册表）
**职责**:
- 扫描技能目录
- 解析 SKILL.md 文件
- 维护技能索引
- 提供技能搜索

**关键类**: `SkillRegistry`, `SkillMetadata`

**关键方法**:
- `discover_skills()` - 发现技能
- `get_skill()` - 获取技能
- `search_skills()` - 搜索技能
- `get_skills_summary()` - 生成技能摘要

### 3. src/injector.py（技能注入器）
**职责**:
- 动态激活技能
- 管理激活状态
- 注入技能内容到上下文
- 智能匹配技能

**关键类**: `SkillInjector`

**关键方法**:
- `activate_skill()` - 激活技能
- `deactivate_skill()` - 停用技能
- `build_context_injection()` - 构建上下文注入
- `match_skill_by_query()` - 匹配技能

### 4. src/mcp_client.py（MCP 客户端）
**职责**:
- 连接 MCP 服务器
- 调用 MCP 工具
- 搜索文档
- 获取文档内容

**关键类**: `MCPClient`, `MCPTool`

**关键方法**:
- `initialize()` - 初始化连接
- `call_tool()` - 调用工具
- `search_docs()` - 搜索文档
- `fetch_doc()` - 获取文档

### 5. src/system_prompts.py（系统提示管理器）
**职责**:
- 生成系统提示
- 动态更新提示
- 管理提示模板
- 提供工具说明

**关键类**: `SystemPromptsManager`

**关键方法**:
- `build_system_prompt()` - 构建系统提示
- `update_for_query()` - 根据查询更新
- `get_tools_instruction()` - 获取工具说明

## 数据流

```
用户输入
    ↓
main.py (CLI)
    ↓
AzureDocAgent.chat()
    ↓
SystemPromptsManager.update_for_query()
    ↓
SkillInjector.build_context_injection()
    ↓
SkillRegistry.search_skills()
    ↓
准备消息 + 系统提示
    ↓
AzureDocAgent._call_llm()
    ↓
Azure OpenAI API
    ↓
检查工具调用？
    ├─ 是 → _handle_tool_calls()
    │         ↓
    │    _execute_tool()
    │         ├─ activate_skill() → SkillInjector
    │         ├─ search_microsoft_docs() → MCPClient
    │         ├─ fetch_microsoft_doc() → MCPClient
    │         └─ list_available_skills() → SkillRegistry
    │         ↓
    │    再次调用 LLM
    └─ 否 → 直接返回
    ↓
返回响应给用户
    ↓
更新对话历史
```

## 配置文件

### .env（需创建）
```env
AZURE_OPENAI_ENDPOINT=      # Azure OpenAI 端点
AZURE_OPENAI_KEY=           # API 密钥
AZURE_OPENAI_DEPLOYMENT=    # 部署名称
MCP_SERVER_URL=             # MCP 服务器 URL
SKILLS_DIRECTORY=           # 技能目录路径
LOG_LEVEL=                  # 日志级别
LOG_FILE=                   # 日志文件路径
MAX_HISTORY_LENGTH=         # 最大历史长度
```

## 技能定义格式

### SKILL.md 结构
```markdown
---
name: skill-name
description: 技能描述
context: fork
compatibility: 兼容性说明
tags: ["tag1", "tag2"]
---

# 技能标题

## Tools
工具列表

## When to Use
使用场景

## Query Effectiveness
查询建议

## Why Use This
使用原因
```

## 扩展点

### 1. 添加新技能
在 `.skills/` 目录下创建新文件夹，添加 `SKILL.md`

### 2. 自定义 MCP 服务器
修改 `src/mcp_client.py`，添加新的服务器连接

### 3. 扩展工具
在 `AzureDocAgent._get_tool_definitions()` 中添加新工具

### 4. 自定义提示
修改 `SystemPromptsManager` 中的提示模板

### 5. 添加缓存
在 `MCPClient` 中集成 Redis 缓存

## 依赖关系图

```
main.py
  └── AzureDocAgent
        ├── SkillRegistry
        ├── SkillInjector
        │     └── SkillRegistry
        ├── MCPClient
        ├── SystemPromptsManager
        │     ├── SkillRegistry
        │     └── SkillInjector
        └── AzureOpenAI Client
```


## 日志系统

### 日志级别
- DEBUG: 详细调试信息
- INFO: 一般信息
- WARNING: 警告信息
- ERROR: 错误信息
- CRITICAL: 严重错误

### 日志输出
- 控制台: 彩色格式，INFO 及以上
- 文件: 完整格式，DEBUG 及以上

## 性能考虑

### 异步架构
- 使用 `asyncio` 实现并发
- 所有 I/O 操作异步化
- 支持多个并发请求

### 内存管理
- 对话历史限制（默认 20 条）
- 技能按需加载
- 定期清理未使用的线程

### 网络优化
- HTTP/2 连接复用
- 请求超时控制
- 重试机制

## 安全性

### 密钥管理
- 使用环境变量
- 建议使用 Azure Key Vault
- 不在代码中硬编码

### 输入验证
- 用户输入清理
- 参数验证
- 防止注入攻击

### 日志安全
- 不记录敏感信息
- API 密钥脱敏
- 用户数据保护

## 测试策略

### 单元测试
- 每个模块独立测试
- 使用 pytest
- Mock 外部依赖

### 集成测试
- 端到端流程测试
- MCP 连接测试
- Azure OpenAI 调用测试


