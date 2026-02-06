#!/bin/bash

# 总启动脚本 - Azure Doc Agent
# 一键启动前端 + 后端

cd "$(dirname "$0")"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Azure Doc Agent - 总启动脚本"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境未找到!"
    echo "请先运行: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 2. 检查前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 正在安装前端依赖..."
    cd frontend
    npm install
    cd ..
    echo ""
fi

# 3. 创建日志目录
mkdir -p logs

# 4. 清理函数
cleanup() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🛑 正在关闭 Azure Doc Agent..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 终止后端
    if [ ! -z "$BACKEND_PID" ]; then
        echo "   ⏹️  停止后端服务 (PID: $BACKEND_PID)"
        kill $BACKEND_PID 2>/dev/null
    fi
    
    # 终止前端
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "   ⏹️  停止前端服务 (PID: $FRONTEND_PID)"
        kill $FRONTEND_PID 2>/dev/null
        # Vite可能有子进程，也要清理
        pkill -P $FRONTEND_PID 2>/dev/null
    fi
    
    echo ""
    echo "✅ 所有服务已停止"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# 5. 启动后端
echo "📡 [1/2] 启动后端服务..."
echo "     → 地址: http://localhost:8000"
./venv/bin/python -m uvicorn src.api_server:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "     ✓ 后端进程启动 (PID: $BACKEND_PID)"
echo ""

# 等待后端启动
echo "⏳ 等待后端初始化..."
sleep 4

# 6. 启动前端
echo "🎨 [2/2] 启动前端服务..."
echo "     → 地址: http://localhost:3000"
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "     ✓ 前端进程启动 (PID: $FRONTEND_PID)"
echo ""

# 等待前端启动
sleep 2

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Azure Doc Agent 启动成功!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 访问地址:"
echo "   🌐 前端界面:  http://localhost:3000"
echo "   📡 后端 API:  http://localhost:8000"
echo "   📚 API 文档:  http://localhost:8000/docs"
echo ""
echo "📝 日志文件:"
echo "   📄 应用日志:  logs/agent.log"
echo "   📄 后端日志:  logs/backend.log"
echo "   📄 前端日志:  logs/frontend.log"
echo ""
echo "💡 提示:"
echo "   • 左侧边栏有 5 个中文示例问题，点击即可测试"
echo "   • 按 Ctrl+C 停止所有服务"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 7. 保持运行并等待
wait
