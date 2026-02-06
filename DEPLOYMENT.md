# 部署指南

## 部署到 Azure

### 前置条件

1. Azure 订阅
2. Azure OpenAI 资源
3. Python 3.9+

### 步骤 1: 创建 Azure OpenAI 资源

```bash
# 登录 Azure
az login

# 创建资源组
az group create --name rg-azure-doc-agent --location eastus

# 创建 Azure OpenAI 资源
az cognitiveservices account create \
  --name azure-doc-agent-openai \
  --resource-group rg-azure-doc-agent \
  --kind OpenAI \
  --sku S0 \
  --location eastus
```

### 步骤 2: 部署模型

```bash
# 部署 GPT-4o 模型
az cognitiveservices account deployment create \
  --name azure-doc-agent-openai \
  --resource-group rg-azure-doc-agent \
  --deployment-name gpt-4o \
  --model-name gpt-4o \
  --model-version "2024-05-13" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name "Standard"
```

### 步骤 3: 获取连接信息

```bash
# 获取 endpoint
az cognitiveservices account show \
  --name azure-doc-agent-openai \
  --resource-group rg-azure-doc-agent \
  --query "properties.endpoint" -o tsv

# 获取 key
az cognitiveservices account keys list \
  --name azure-doc-agent-openai \
  --resource-group rg-azure-doc-agent \
  --query "key1" -o tsv
```

### 步骤 4: 配置环境变量

创建 `.env` 文件：

```env
AZURE_OPENAI_ENDPOINT=<从步骤3获取的endpoint>
AZURE_OPENAI_KEY=<从步骤3获取的key>
AZURE_OPENAI_DEPLOYMENT=gpt-4o
MCP_SERVER_URL=https://learn.microsoft.com/api/mcp
SKILLS_DIRECTORY=.skills
LOG_LEVEL=INFO
LOG_FILE=logs/agent.log
MAX_HISTORY_LENGTH=20
```

### 步骤 5: 部署到 Azure Container Instances

创建 `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

构建并推送镜像：

```bash
# 创建 Azure Container Registry
az acr create \
  --resource-group rg-azure-doc-agent \
  --name azuredocagentacr \
  --sku Basic

# 登录 ACR
az acr login --name azuredocagentacr

# 构建镜像
docker build -t azuredocagentacr.azurecr.io/azure-doc-agent:latest .

# 推送镜像
docker push azuredocagentacr.azurecr.io/azure-doc-agent:latest

# 部署到 ACI
az container create \
  --resource-group rg-azure-doc-agent \
  --name azure-doc-agent \
  --image azuredocagentacr.azurecr.io/azure-doc-agent:latest \
  --registry-login-server azuredocagentacr.azurecr.io \
  --registry-username <acr-username> \
  --registry-password <acr-password> \
  --environment-variables \
    AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT \
    AZURE_OPENAI_KEY=$AZURE_OPENAI_KEY \
    AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

## 本地开发

### 安装依赖

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 运行测试

```bash
# 基础功能测试
python test_basic.py

# 完整测试（需要配置 .env）
python -m pytest tests/
```

### 启动应用

```bash
python main.py
```

## Docker 本地运行

```bash
# 构建镜像
docker build -t azure-doc-agent .

# 运行容器
docker run -it --rm \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  azure-doc-agent
```

## 故障排查

### 常见问题

1. **MCP 连接失败**
   - 检查网络连接
   - 验证 MCP_SERVER_URL 配置

2. **Azure OpenAI 调用失败**
   - 检查 API key 和 endpoint
   - 验证模型部署名称
   - 检查配额限制

3. **技能未发现**
   - 确认 .skills 目录存在
   - 检查 SKILL.md 文件格式

### 日志调试

```bash
# 查看实时日志
tail -f logs/agent.log

# 调整日志级别
export LOG_LEVEL=DEBUG
python main.py
```

## 性能优化

### 缓存配置

可以添加 Redis 缓存来优化性能：

```python
# 在 mcp_client.py 中添加缓存
import redis

cache = redis.Redis(host='localhost', port=6379, db=0)
```

### 并发优化

使用 `aiohttp` 和 `asyncio` 来提高并发性能：

```python
# 已在代码中实现异步架构
```

## 监控

### Azure Application Insights

```bash
# 添加依赖
pip install opencensus-ext-azure

# 配置
export APPLICATIONINSIGHTS_CONNECTION_STRING=<connection-string>
```

## 安全

### 密钥管理

使用 Azure Key Vault 管理敏感信息：

```bash
# 创建 Key Vault
az keyvault create \
  --name azure-doc-agent-kv \
  --resource-group rg-azure-doc-agent \
  --location eastus

# 存储密钥
az keyvault secret set \
  --vault-name azure-doc-agent-kv \
  --name azure-openai-key \
  --value <your-key>
```

修改代码使用 Key Vault：

```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://azure-doc-agent-kv.vault.azure.net/", credential=credential)
api_key = client.get_secret("azure-openai-key").value
```
