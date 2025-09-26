#!/bin/bash

# 🚀 IIMS Analytics Agent - Node.js 18 Startup Script
# Ensures correct Node.js version and starts the server

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

echo "🚀 Starting IIMS Analytics Agent with Node.js 18"
echo "================================================"

# Load nvm
if [ -s "$HOME/.nvm/nvm.sh" ]; then
    print_status "Loading NVM..."
    source "$HOME/.nvm/nvm.sh"
    
    # Use Node.js 18
    print_status "Switching to Node.js 18..."
    nvm use 18
    
    # Force correct PATH
    export PATH="$NVM_BIN:$PATH"
    
    print_success "Using Node.js $(node --version) from $(which node)"
    print_success "Using npm $(npm --version) from $(which npm)"
else
    print_error "NVM not found! Please install nvm first."
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_warning "node_modules not found. Installing dependencies..."
    npm install
fi

# Build if needed
if [ ! -d "dist" ] || [ "src/index.ts" -nt "dist/index.js" ]; then
    print_status "Building TypeScript..."
    npm run build
fi

# Start the server
print_status "Starting server on port 3000..."
npm start
