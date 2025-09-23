#!/bin/bash

# Intelligent Sales Analytics Agent Startup Script
# Handles virtual environment setup and server startup

set -e

echo "🚀 Starting Sales Analytics Assistant..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating Python virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "📝 Please edit .env file with your OpenAI API key and other settings"
    else
        echo "❌ .env.example not found. Please create .env file manually."
        exit 1
    fi
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Test Python tools
echo "🧪 Testing Python tools..."
python test_runner.py

# Check if Node.js dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Build TypeScript
echo "🔨 Building TypeScript..."
npm run build

# Start the server
echo "🎯 Starting ChatGPT-like server on port ${PORT:-3000}..."
echo "💬 Chat endpoint: http://localhost:${PORT:-3000}/chat"
echo "📊 Health check: http://localhost:${PORT:-3000}/health"
echo ""
echo "🔥 Ready for sales analytics conversations!"
echo "Press Ctrl+C to stop the server"
echo ""

# Start server with proper environment
npm run start
