#!/bin/bash

# Demo script for the Sales Analytics Assistant
# Tests the complete ChatGPT-like interface

echo "🎯 Sales Analytics Assistant Demo"
echo "================================="

# Check if server is running
echo "🔍 Checking if server is running on port 3000..."
if curl -s http://localhost:3000/health > /dev/null; then
    echo "✅ Server is running!"
else
    echo "❌ Server not running. Start it first with: ./start.sh"
    exit 1
fi

echo ""
echo "🧪 Running Chat Tests..."
echo "------------------------"

# Test 1: Sales Trends
echo ""
echo "📊 Test 1: Sales Trends Analysis"
echo "User: 'Show me sales trends for last month'"
curl -s -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me sales trends for last month",
    "session_id": "demo_session_1"
  }' | jq '.message' | head -c 200
echo "..."
echo ""

# Test 2: Product Performance
echo "🏆 Test 2: Product Performance"
echo "User: 'Which menu items are performing best?'"
curl -s -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Which menu items are performing best?",
    "session_id": "demo_session_2"
  }' | jq '.message' | head -c 200
echo "..."
echo ""

# Test 3: Sales Forecasting
echo "🔮 Test 3: Sales Forecasting"
echo "User: 'Predict Kerala Burger sales for next 30 days'"
curl -s -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Predict Kerala Burger sales for next 30 days",
    "session_id": "demo_session_3"
  }' | jq '.message' | head -c 200
echo "..."
echo ""

# Test 4: Period Comparison
echo "📊 Test 4: Period Comparison"
echo "User: 'Compare this month vs last month revenue'"
curl -s -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Compare this month vs last month revenue",
    "session_id": "demo_session_4"
  }' | jq '.message' | head -c 200
echo "..."
echo ""

# Test 5: Follow-up Context
echo "🔄 Test 5: Follow-up Context"
echo "First message: 'Show me Kerala Burger performance'"
curl -s -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me Kerala Burger performance",
    "session_id": "demo_session_5"
  }' > /dev/null

echo "Follow-up: 'What about next month forecast for that?'"
curl -s -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What about next month forecast for that?",
    "session_id": "demo_session_5"
  }' | jq '.message' | head -c 200
echo "..."
echo ""

# Test 6: Help
echo "💡 Test 6: Help"
echo "User: 'What can you help me with?'"
curl -s -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What can you help me with?",
    "session_id": "demo_session_6"
  }' | jq '.message'
echo ""

# Test session history
echo "📜 Test 7: Session History"
echo "Getting conversation history for demo_session_5..."
curl -s -X GET http://localhost:3000/chat/demo_session_5/history | jq '.metadata'
echo ""

echo "🎉 Demo completed!"
echo ""
echo "💡 Try these examples:"
echo "  curl -X POST http://localhost:3000/chat -H 'Content-Type: application/json' -d '{\"message\":\"Show sales trends\",\"session_id\":\"my_session\"}'"
echo "  curl -X POST http://localhost:3000/chat -H 'Content-Type: application/json' -d '{\"message\":\"Predict next month sales\",\"session_id\":\"my_session\"}'"
echo "  curl -X POST http://localhost:3000/chat -H 'Content-Type: application/json' -d '{\"message\":\"Which products sell best?\",\"session_id\":\"my_session\"}'"
echo ""
echo "🌐 Or test in browser: http://localhost:3000/health"
