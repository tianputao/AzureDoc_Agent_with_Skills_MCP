#!/bin/bash

# 快速启动脚本

echo "=================================================="
echo "Azure Doc Agent - 快速安装"
echo "=================================================="
echo ""

# 1. 创建虚拟环境
echo "📦 创建虚拟环境..."
python3 -m venv venv

# 2. 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 3. 升级 pip
echo "⬆️  升级 pip..."
pip install --upgrade pip

# 4. 安装依赖
echo "📥 安装依赖包..."
pip install -r requirements.txt

# 5. 创建 .env 文件
if [ ! -f .env ]; then
    echo "📝 创建 .env 文件..."
    cp .env.example .env
    echo ""
    echo "⚠️  请编辑 .env 文件并配置以下变量:"
    echo "   - AZURE_OPENAI_ENDPOINT"
    echo "   - AZURE_OPENAI_KEY"
    echo "   - AZURE_OPENAI_DEPLOYMENT"
    echo ""
fi

# 6. 创建日志目录
mkdir -p logs

echo "=================================================="
echo "✅ 安装完成！"
echo "=================================================="
echo ""
echo "下一步:"
echo "1. 编辑 .env 文件配置 Azure OpenAI"
echo "2. 运行测试: python test_basic.py"
echo "3. 启动应用: python main.py"
echo ""
echo "文档:"
echo "- 快速开始: cat QUICKSTART.md"
echo "- 使用示例: cat EXAMPLES.md"
echo "- 完整文档: cat README.md"
echo ""
