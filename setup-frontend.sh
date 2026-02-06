#!/bin/bash

# Setup script for frontend

echo "📦 Setting up React frontend..."
echo ""

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
else
    echo "Dependencies already installed"
fi

echo ""
echo "✅ Frontend setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure backend: cp .env.example .env && edit .env"
echo "2. Install Python deps: pip install -r requirements.txt"
echo "3. Start servers: ./start.sh"
