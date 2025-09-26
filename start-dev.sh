#!/bin/bash

# 🚀 IIMS Development Server with Hot Reload
# Starts both Node.js and Python components with automatic reload on file changes

set -e

echo "🚀 Starting IIMS Development Server with Hot Reload..."
echo "======================================================="

# Colors for better output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
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

print_dev() {
    echo -e "${PURPLE}[DEV]${NC} $1"
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found!"
    echo ""
    echo "🔧 Please create a virtual environment first:"
    echo "   python3.11 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
print_status "Activating Python virtual environment..."
source venv/bin/activate

# Check Python version
PYTHON_VERSION=$(python --version 2>&1)
print_success "Using: $PYTHON_VERSION"

# Install/Update dependencies if needed
print_status "Checking and updating dependencies..."

# Check if Node dependencies need updating
if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules" ]; then
    print_status "Installing/updating Node.js dependencies..."
    npm install
    print_success "Node.js dependencies updated"
else
    print_success "Node.js dependencies are up to date"
fi

# Check if Python dependencies need updating
print_status "Checking Python dependencies..."
pip install -r requirements.txt --quiet
print_success "Python dependencies verified"

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from env.example..."
    if [ -f "env.example" ]; then
        cp env.example .env
        print_success ".env file created from template"
        echo "📝 Please edit .env file with your settings before proceeding"
    else
        print_error "env.example not found. Please create .env file manually"
        exit 1
    fi
fi

# Load environment variables
print_status "Loading environment variables..."
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
    print_success "Environment variables loaded"
else
    print_error "Failed to load .env file"
    exit 1
fi

# Make scripts executable
chmod +x scripts/*.py scripts/*.js 2>/dev/null || true

# Check for required tools
print_status "Verifying development tools..."

# Check if concurrently is available
if ! npm list concurrently --depth=0 >/dev/null 2>&1; then
    print_warning "Installing concurrently for process management..."
    npm install concurrently --save-dev
fi

# Check if chokidar is available
if ! npm list chokidar --depth=0 >/dev/null 2>&1; then
    print_warning "Installing chokidar for file watching..."
    npm install chokidar --save-dev
fi

# Verify Python watchdog
if ! python -c "import watchdog" 2>/dev/null; then
    print_warning "Installing Python watchdog for file monitoring..."
    pip install watchdog
fi

print_success "Development tools verified"

# Display configuration
echo ""
print_dev "🔧 Development Configuration:"
print_dev "================================"
print_dev "📂 Project: $(pwd)"
print_dev "🐍 Python: $(python --version)"
print_dev "📦 Node.js: $(node --version)"
print_dev "🔥 Hot Reload: TypeScript + Python"
print_dev "📱 Server Port: ${PORT:-3000}"
print_dev "🌐 Environment: development"
print_dev "👁️  File Watching: Active"

echo ""
print_dev "🎯 Hot Reload Features:"
print_dev "========================"
print_dev "✅ TypeScript files (.ts) - Automatic server restart"
print_dev "✅ Python files (.py) - Module cache clearing + restart"
print_dev "✅ LangGraph flows - Real-time updates"
print_dev "✅ Tools and nodes - Instant reload"
print_dev "✅ Configuration files - Automatic pickup"

echo ""
print_dev "📡 Available Endpoints:"
print_dev "======================="
print_dev "💬 Chat: http://localhost:${PORT:-3000}/chat"
print_dev "🏥 Health: http://localhost:${PORT:-3000}/health"
print_dev "📊 Analytics: http://localhost:${PORT:-3000}/analytics"

echo ""
print_dev "⌨️  Development Commands:"
print_dev "========================="
print_dev "🛑 Stop server: Ctrl+C"
print_dev "🔄 Force restart: rs + Enter (in nodemon)"
print_dev "📝 View logs: Check terminal output"

echo ""
print_success "🚀 Starting development server with hot reload..."
print_dev "🔄 Both TypeScript and Python changes will trigger automatic reloads"
print_dev "💡 Make changes to any .ts or .py file to see hot reload in action"
echo ""

# Set development environment
export NODE_ENV=development
export ENABLE_STREAMING=true

# Start the development server with hot reload
# This will run both the Node.js server with nodemon and the Python file watcher
exec npm run dev:full
