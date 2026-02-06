#!/bin/bash

# Start Frontend Script for Azure Doc Agent

cd "$(dirname "$0")/frontend"

echo "🎨 Starting Azure Doc Agent Frontend..."
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
    echo ""
fi

echo "🌐 Starting development server on http://localhost:3000"
echo ""

npm run dev
