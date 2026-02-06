# 📚 Azure Doc Agent - 文档导航

欢迎使用 Azure Doc Agent！这是一个集成了 Agent Skills 和 MCP 的智能文档助手。

## 🚀 快速导航

### 🎯 我想立即开始使用
→ **[QUICKSTART.md](QUICKSTART.md)** - 5 分钟快速开始指南

### 📖 我想了解项目概况
→ **[README.md](README.md)** - 完整的项目说明文档

### 💡 我想看使用示例
→ **[README.md](README.md#-使用示例)** - 查看 README 中的代码示例

### 🏗️ 我想了解架构设计
→ **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - 项目结构和架构详解

### 🚢 我想部署到生产环境
→ **[DEPLOYMENT.md](DEPLOYMENT.md)** - 部署指南和最佳实践

### 📊 我想查看架构文档
→ **[docs/](docs/)** - 博客文章、架构图表等

---

## 📁 文件说明

### 核心代码
- `src/azure_doc_agent.py` - 主 Agent 类，核心功能实现
- `src/registry.py` - 技能注册表，管理技能发现和索引
- `src/injector.py` - 技能注入器，动态加载技能
- `src/mcp_client.py` - MCP 客户端，连接文档服务器
- `src/system_prompts.py` - 系统提示管理器

### 技能定义
- `skills/microsoft-docs/SKILL.md` - 文档搜索技能
- `skills/microsoft-code-reference/SKILL.md` - 代码参考技能

### 可执行文件
- `main.py` - 主程序入口（交互式 CLI）
- `test_basic.py` - 基础功能测试脚本
- `setup.sh` - 自动安装脚本
- `verify.sh` - 项目验证脚本

### 配置文件
- `requirements.txt` - Python 依赖包列表
- `.env.example` - 环境变量配置示例
- `Dockerfile` - Docker 容器配置
- `docker-compose.yml` - Docker Compose 配置

---

## 🎓 学习路径

### 第一步：安装和配置（5 分钟）
1. 阅读 [QUICKSTART.md](QUICKSTART.md)
2. 运行 `./setup.sh` 或手动安装依赖
3. 配置 `.env` 文件

### 第二步：基础使用（10 分钟）
1. 运行 `python test_basic.py` 测试功能
2. 启动 `python main.py` 开始对话
3. 尝试基本命令：`/help`, `/skills`, `/threads`

### 第三步：深入理解（30 分钟）
1. 阅读 [README.md](README.md) 了解完整功能
2. 查看 [docs/BLOG_POST_CN.md](docs/BLOG_POST_CN.md) 学习架构设计
3. 研究 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) 理解代码结构

### 第四步：生产部署（1 小时）
1. 阅读 [DEPLOYMENT.md](DEPLOYMENT.md)
2. 选择部署方式（本地/Docker/Azure）
3. 配置监控和日志

---

## 🔧 常用操作

### 安装依赖
```bash
./setup.sh
# 或
pip install -r requirements.txt
```

### 验证项目
```bash
./verify.sh
```

### 运行测试
```bash
python test_basic.py
```

### 启动应用
```bash
python main.py
```

### Docker 运行
```bash
docker-compose up
```

---

## 📞 获取帮助

### 查看日志
```bash
tail -f logs/agent.log
```

### 调试模式
```bash
export LOG_LEVEL=DEBUG
python main.py
```

### 检查配置
```bash
cat .env
```

---

## 🎯 核心功能

### ✅ Agent Skills
- 自动发现技能（`skills/` 目录）
- 动态注入技能内容
- 智能匹配相关技能

### ✅ MCP 集成
- 连接 Microsoft Learn MCP Server
- 搜索官方文档
- 获取完整页面内容

### ✅ 多轮对话
- 线程管理（支持多个独立对话）
- 上下文维护
- 对话历史记录

### ✅ 异步架构
- 高性能并发
- 非阻塞 I/O
- 流式响应

---

## 📊 项目统计

- **代码行数**: ~1,900 行
- **文件数量**: 23 个
- **技能数量**: 2 个（可扩展）
- **文档页数**: 8 个

---

## 🔗 相关链接

- [Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/)
- [Agent Skills Standard](https://agentskills.io)
- [Microsoft Learn MCP](https://learn.microsoft.com/api/mcp)
- [Azure OpenAI Service](https://azure.microsoft.com/products/ai-services/openai-service)

---

## 🎊 开始探索！

选择一个起点，开始你的 Azure Doc Agent 之旅：

- 🏃 [快速开始](QUICKSTART.md) - 立即开始
- 📖 [完整文档](README.md) - 深入了解
- � [博客文章](docs/BLOG_POST_CN.md) - 了解架构
- 🏗️ [项目结构](PROJECT_STRUCTURE.md) - 理解代码
- 🚀 [部署指南](DEPLOYMENT.md) - 投入生产

---

**祝你使用愉快！** 🎉

如有问题，请查看相应文档或查看日志文件。
