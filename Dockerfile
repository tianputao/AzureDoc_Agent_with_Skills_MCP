FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（包括 Node.js for frontend）
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
COPY frontend/package*.json ./frontend/

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装前端依赖
WORKDIR /app/frontend
RUN npm ci

# 返回工作目录
WORKDIR /app

# 复制项目文件
COPY . .

# 构建前端
WORKDIR /app/frontend
RUN npm run build

# 返回根目录
WORKDIR /app

# 创建日志目录
RUN mkdir -p logs

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV LOG_FILE=/app/logs/agent.log

# 暴露端口
EXPOSE 8000
EXPOSE 3000

# 运行应用（Web 模式）
# 使用 start.sh 启动前端+后端
CMD ["bash", "start.sh"]

