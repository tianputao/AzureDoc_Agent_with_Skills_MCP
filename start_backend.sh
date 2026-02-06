#!/bin/bash

# Start Backend Script for Azure Doc Agent

cd "$(dirname "$0")"

echo "🚀 Starting Azure Doc Agent Backend..."
echo ""

# Create logs directory
mkdir -p logs

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Start backend with uvicorn
echo "📡 Starting API server on http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/docs"
echo ""

./venv/bin/python -m uvicorn src.api_server:app --host 0.0.0.0 --port 8000 --reload
