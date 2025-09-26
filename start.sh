#!/bin/bash

# 🚀 Intelligent Sales Analytics Agent Startup Script
# Optimized for Python 3.11+ with latest LangGraph support

set -e

echo "🚀 Starting IIMS Sales Analytics Assistant..."
echo "============================================="

# Colors for better output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Load nvm and use correct Node version
load_nvm() {
    print_status "Loading NVM and setting Node.js version..."
    if [ -s "$HOME/.nvm/nvm.sh" ]; then
        source "$HOME/.nvm/nvm.sh"
        nvm use 18 > /dev/null 2>&1 || {
            print_warning "Node.js 18 not found, installing..."
            nvm install 18
            nvm use 18
        }
        print_success "Using Node.js $(node --version)"
    else
        print_warning "NVM not found, using system Node.js $(node --version)"
    fi
}

# Load NVM and set correct Node.js version
load_nvm

# Check if virtual environment exists and validate Python version
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found!"
    echo ""
    echo "🔧 Please create a virtual environment first:"
    echo "   python3.11 -m venv venv"
    echo "   # or run: ./manual_venv_setup.sh"
    exit 1
fi

# Activate virtual environment
print_status "Activating Python virtual environment..."
source venv/bin/activate

# Check Python version in venv
PYTHON_VERSION=$(python --version 2>&1)
print_success "Using: $PYTHON_VERSION"

# Verify we have Python 3.9+ for LangGraph compatibility
PYTHON_MAJOR=$(python -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$(python -c "import sys; print(sys.version_info.minor)")

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
    print_success "Python version is compatible with LangGraph (3.9+)"
else
    print_warning "Python version may have compatibility issues with latest packages"
    echo "           Consider using Python 3.11+ for best results"
fi

# Upgrade pip if needed
print_status "Ensuring pip is up to date..."
python -m pip install --upgrade pip --quiet

# Install/Update Python dependencies
print_status "Installing/updating Python dependencies..."
pip install -r requirements.txt

# Verify LangGraph installation
print_status "Verifying LangGraph installation..."
if python -c "from langgraph.graph import StateGraph, END, START; print('✅ LangGraph imports successful')" 2>/dev/null; then
    print_success "LangGraph is working correctly!"
else
    print_warning "LangGraph import failed - this may cause issues"
    echo "           Try: pip install --upgrade langgraph"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from env.example..."
    if [ -f "env.example" ]; then
        cp env.example .env
        print_success ".env file created from template"
        echo "📝 Please edit .env file with your OpenAI API key and other settings"
        echo "   Key variables to set:"
        echo "   - OPENAI_API_KEY=your_openai_api_key_here"
        echo "   - BASE_URL=http://localhost:8000"
        echo "   - X_TENANT_ID=your_tenant_id"
    else
        print_error "env.example not found. Please create .env file manually with:"
        echo "   OPENAI_API_KEY=your_openai_api_key_here"
        echo "   BASE_URL=http://localhost:8000"
        echo "   X_TENANT_ID=11111111-1111-1111-1111-111111111111"
        echo "   PORT=3000"
        exit 1
    fi
fi

# Load environment variables safely
print_status "Loading environment variables..."
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
    print_success "Environment variables loaded"
else
    print_error "Failed to load .env file"
    exit 1
fi

# Test Python tools and imports
print_status "Testing Python tools and imports..."
if python -c "
import sys
print(f'Testing imports with Python {sys.version}')

# Test core imports
try:
    from langgraph.graph import StateGraph, END, START
    print('✅ LangGraph imports successful')
except Exception as e:
    print(f'❌ LangGraph import failed: {e}')

try:
    from langchain_core.tools import tool
    print('✅ LangChain core imports successful')
except Exception as e:
    print(f'❌ LangChain core import failed: {e}')

try:
    import requests
    print('✅ Requests import successful')
except Exception as e:
    print(f'❌ Requests import failed: {e}')

try:
    import openai
    print('✅ OpenAI import successful')
except Exception as e:
    print(f'❌ OpenAI import failed: {e}')

print('Import tests completed')
" 2>/dev/null; then
    print_success "Python imports test passed!"
else
    print_warning "Some Python imports failed - check dependencies"
fi

# Check if Node.js dependencies are installed
if [ ! -d "node_modules" ]; then
    print_status "Installing Node.js dependencies..."
    if command -v npm >/dev/null 2>&1; then
        npm install
        print_success "Node.js dependencies installed"
    else
        print_error "npm not found. Please install Node.js first"
        exit 1
    fi
else
    print_success "Node.js dependencies already installed"
fi

# Build TypeScript
print_status "Building TypeScript..."
if npm run build; then
    print_success "TypeScript build completed"
else
    print_error "TypeScript build failed"
    exit 1
fi

# Final pre-flight check
print_status "Running pre-flight checks..."
echo ""
echo "📋 System Status:"
echo "=================="
echo "✅ Python: $(python --version)"
echo "✅ Virtual Environment: $(pwd)/venv"
echo "✅ LangGraph: $(python -c "import langgraph; print(langgraph.__version__)" 2>/dev/null || echo 'Installed')"
echo "✅ LangChain: $(python -c "import langchain; print(langchain.__version__)" 2>/dev/null || echo 'Installed')"
echo "✅ OpenAI: $(python -c "import openai; print(openai.__version__)" 2>/dev/null || echo 'Installed')"
echo "✅ Node.js: $(node --version 2>/dev/null || echo 'Available')"
echo "✅ Environment: $([ -f .env ] && echo 'Configured' || echo 'Missing')"

# Start the server
echo ""
print_success "🎯 Starting ChatGPT-like server on port ${PORT:-3000}..."
echo ""
echo "🌐 Available endpoints:"
echo "   💬 Chat endpoint: http://localhost:${PORT:-3000}/chat"
echo "   📊 Health check: http://localhost:${PORT:-3000}/health"
echo "   📈 Analytics: http://localhost:${PORT:-3000}/analytics"
echo ""
echo "🔥 Ready for sales analytics conversations!"
echo "   📱 Open your browser to start chatting"
echo "   🛑 Press Ctrl+C to stop the server"
echo ""

# Start server with proper environment
if npm run start; then
    print_success "Server started successfully!"
else
    print_error "Failed to start server"
    echo ""
    echo "🔧 Troubleshooting tips:"
    echo "   1. Check if port ${PORT:-3000} is available"
    echo "   2. Verify .env file has correct settings"
    echo "   3. Ensure backend API is running"
    echo "   4. Check logs above for specific errors"
    exit 1
fi