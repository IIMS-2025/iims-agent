# Intelligent Sales Analytics Conversational Assistant

A ChatGPT-like conversational AI assistant for sales analysis and forecasting using LangGraph orchestration with tool-based database access and OpenAI integration.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Environment & Configuration](#environment--configuration)
- [High-level LangGraph Requirements](#high-level-langgraph-requirements)
- [Exact API Call Templates](#exact-api-call-templates)
- [Prompting Rules for OpenAI/LLM Node](#prompting-rules-for-openaillm-node)
- [Slot-filling & Conversation Patterns](#slot-filling--conversation-patterns)
- [Normalization & Reply Rules](#normalization--reply-rules)
- [Node/TypeScript Minimal Server](#nodetypescript-minimal-server)
- [Test Harness & Sample Utterances](#test-harness--sample-utterances)
- [Error Handling & Validation Strategy](#error-handling--validation-strategy)
- [Session Management & Follow-ups](#session-management--follow-ups)
- [Security & Operational Considerations](#security--operational-considerations)
- [Acceptance Criteria](#acceptance-criteria)
- [Future Improvements](#future-improvements)
- [Repository Layout](#repository-layout)
- [Implementation Instructions](#implementation-instructions)

---

## Overview

**Goal**: Build an MVP ChatGPT-like conversational assistant that enables natural language interaction for sales analytics and forecasting for Kochi Burger Junction.

### Key Features:

- **Sales Analysis** - Analyze historical sales data, trends, and patterns
- **Forecasting** - Predict future sales based on historical data and seasonality
- **Inventory Insights** - View current stock levels and make data-driven recommendations
- **Product Performance** - Analyze best/worst performing menu items and raw materials
- **Interactive Charts** - Generate data visualizations and reports through conversation
- **Tool-based Database Access** - All data queries executed as LangGraph tools
- **Session-aware** conversations with follow-up context and data continuity
- **No RAG, no vector DB** - uses session-only context in memory with optional Redis toggle

### Technology Stack:

- **LangGraph** with tool-based architecture for conversation flow orchestration
- **OpenAI API** with function calling for natural language understanding and response generation
- **Node.js/TypeScript** server as ChatGPT-like interface with streaming support
- **Tool-based Database Access** - All queries as LangGraph tools (no direct API calls)
- **In-memory sessions** with conversation history and data context (configurable Redis backend)

### Deliverables:

1. LangGraph project with conversation flows and database tool integrations
2. Node/TypeScript server with ChatGPT-like chat interface and streaming responses
3. OpenAI function calling integration with sales analytics tools
4. Database tool definitions for all sales/inventory queries
5. Comprehensive test suite with sales analysis conversations
6. Data visualization helpers and chart generation utilities

---

## Architecture

```
ChatGPT-like Frontend → Node/TS Server → LangGraph Flow → OpenAI Function Calling
                             ↓                ↓
                      Session Store    Database Tools
                      (Memory/Redis)   (Sales/Inventory)
```

### Components:

- **LangGraph Project**: Conversation flows with tool-based database access and sales analytics
- **Node/TypeScript Server**: ChatGPT-like interface with `/chat` endpoint and streaming responses
- **Database Tools**: LangGraph tools for all sales, inventory, and analytics queries
- **Session Store**: In-memory conversation history with data context (Redis toggle for production)
- **OpenAI Function Calling**: Advanced prompt engineering with tool definitions and response streaming
- **Analytics Engine**: Sales forecasting and trend analysis capabilities

### Security Considerations:

- API keys never logged or exposed
- File upload sanitization and size limits
- Rate limiting on endpoints and OpenAI calls
- CORS configuration for frontend integration
- Input validation and SQL injection prevention

---

## Environment & Configuration

### Required Environment Variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
ENABLE_STREAMING=true

# Backend API Configuration (for LangGraph tools)
BASE_URL=http://localhost:8000
X_TENANT_ID=11111111-1111-1111-1111-111111111111
ASSET_PREFIX=http://localhost:4566/iims-media/

# Analytics Configuration
FORECAST_DAYS_DEFAULT=30
SALES_HISTORY_DAYS=90
ENABLE_CHARTS=true

# Session Management
SESSION_TTL_SECONDS=3600
REDIS_URL=redis://localhost:6379
MAX_CONVERSATION_HISTORY=20

# Server Configuration
PORT=3000
NODE_ENV=development
CORS_ORIGIN=http://localhost:3001
```

### Example `.env` file:

```bash
# Copy this to .env in your project root
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
ENABLE_STREAMING=true
BASE_URL=http://localhost:8000
X_TENANT_ID=11111111-1111-1111-1111-111111111111
ASSET_PREFIX=http://localhost:4566/iims-media/
FORECAST_DAYS_DEFAULT=30
SALES_HISTORY_DAYS=90
ENABLE_CHARTS=true
SESSION_TTL_SECONDS=3600
MAX_CONVERSATION_HISTORY=20
PORT=3000
NODE_ENV=development
CORS_ORIGIN=http://localhost:3001
```

---

## High-level LangGraph Requirements

### Required Flows and Nodes:

#### 1. Entry Flow

- **Purpose**: Receives user input and routes to appropriate handler
- **Input**: `{ message: string, session_id: string, image?: file }`
- **Output**: Routes to NLU node or direct image processing

#### 2. NLU Intent Extraction Node

- **Purpose**: Classify user intent from natural language for sales analytics
- **Input**: User message text
- **Output**: Intent classification with confidence score
- **Supported Intents**:
  - `analyze_sales_trends` - "Show me sales trends for last month", "How are burger sales performing?"
  - `forecast_sales` - "Predict next month's sales", "What will tomato usage be next week?"
  - `view_inventory_status` - "What's low on stock?", "Show current inventory levels"
  - `analyze_product_performance` - "Which menu items sell the most?", "Show worst performing products"
  - `compare_periods` - "Compare this month vs last month", "Sales difference year over year"
  - `view_specific_metrics` - "Show revenue for Kerala Burger", "Profit margin analysis"
  - `generate_report` - "Create a sales report", "Weekly performance summary"
  - `create_chart` - "Show me a chart of daily sales", "Graph inventory turnover"
  - `update_stock_single` - "Add 20 kg to tomatoes" (basic inventory management)
  - `help` - "What can you analyze?", "Show me examples"
  - `fallback` - Unrecognized intent
  - `clarify` - Ambiguous or incomplete request

#### 3. Parameter Extraction/Slot-filling Node

- **Purpose**: Extract required parameters for database tools and analytics queries
- **Input**: User message + intent
- **Output**: Structured slots object
- **Analytics Slots**:
  - `time_period` (string: "last_week", "last_month", "last_quarter", "custom")
  - `start_date` (ISO string)
  - `end_date` (ISO string)
  - `product_name` (string)
  - `product_id` (UUID, resolved from name)
  - `product_category` (string: "menu", "raw_material", "sub_product")
  - `metric_type` (enum: revenue, quantity_sold, profit_margin, turnover_rate)
  - `forecast_days` (number: 7, 30, 90)
  - `comparison_period` (string: previous period for comparison)
  - `chart_type` (enum: line, bar, pie, trend)
  - `group_by` (enum: day, week, month, product, category)
- **Inventory Slots** (for basic management):
  - `qty` (number)
  - `unit` (string: kg, pcs, ml, etc.)
  - `tx_type` (enum: purchase, usage, adjustment)
  - `reason` (string)

#### 4. Decision/Orchestration Node

- **Purpose**: Determine which database tools to call and orchestrate complex analytics workflows
- **Input**: Intent + filled slots
- **Output**: Route to appropriate tool calls or direct LLM response

#### 5. Database Tool Nodes (LangGraph Tools)

- **Sales Analytics Tool**: Query sales data, trends, and performance metrics
- **Forecasting Tool**: Generate sales predictions and demand forecasting
- **Inventory Status Tool**: Get current inventory levels and stock analysis
- **Product Performance Tool**: Analyze menu item and ingredient performance
- **Comparison Tool**: Compare metrics across different time periods
- **Report Generation Tool**: Create structured reports and summaries
- **Chart Data Tool**: Generate data for visualization (JSON format for charts)
- **Stock Update Tool**: Basic inventory management operations

#### 6. LLM Response Node

- **Purpose**: Generate natural language responses using OpenAI
- **Input**: User context + API results + session history
- **Output**: Natural language response for user

#### 7. Session Context Node

- **Purpose**: Manage conversation state and context
- **Input**: Current interaction data
- **Output**: Updated session with last N messages and selected products
- **Storage**: Last 5 interactions, last selected product_id, session TTL

#### 8. Fallback & Clarify Node

- **Purpose**: Handle missing parameters and provide suggestions
- **Input**: Incomplete slots or unrecognized intent
- **Output**: Clarifying questions with quick-reply suggestions

---

## LangGraph Database Tool Definitions

### Sales Analytics Tool

```python
from langchain_core.tools import tool
import requests
from typing import Optional, Dict, Any

@tool
def analyze_sales_data(
    time_period: str = "last_month",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    product_id: Optional[str] = None,
    category: Optional[str] = None,
    group_by: str = "day"
) -> Dict[str, Any]:
    """
    Analyze sales trends and patterns for specified time periods and products.

    Args:
        time_period: Predefined period (last_week, last_month, last_quarter)
        start_date: Custom start date (ISO format)
        end_date: Custom end date (ISO format)
        product_id: Specific product to analyze
        category: Product category filter
        group_by: Aggregation level (day, week, month)

    Returns:
        Sales data with trends, totals, and insights
    """
    # Implementation calls backend API with analytics parameters
    pass
```

### Forecasting Tool

```python
@tool
def forecast_sales(
    product_id: Optional[str] = None,
    category: Optional[str] = None,
    forecast_days: int = 30,
    include_confidence: bool = True
) -> Dict[str, Any]:
    """
    Generate sales forecasts based on historical data and trends.

    Args:
        product_id: Specific product to forecast
        category: Product category to forecast
        forecast_days: Number of days to forecast (7, 30, 90)
        include_confidence: Include confidence intervals

    Returns:
        Forecast data with predictions and confidence levels
    """
    # Implementation uses historical sales data for ML predictions
    pass
```

### Inventory Status Tool

```python
@tool
def get_inventory_status(
    filter_status: Optional[str] = None,
    product_id: Optional[str] = None,
    include_batches: bool = False
) -> Dict[str, Any]:
    """
    Get current inventory levels and stock status information.

    Args:
        filter_status: Filter by status (low_stock, out_of_stock, expiring_soon)
        product_id: Specific product inventory
        include_batches: Include batch and expiry details

    Returns:
        Current inventory data with stock status and recommendations
    """
    url = f"{BASE_URL}/api/v1/inventory"
    if product_id:
        url += f"/{product_id}"

    headers = {
        "X-Tenant-ID": X_TENANT_ID,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    return response.json()
```

### Product Performance Tool

```python
@tool
def analyze_product_performance(
    time_period: str = "last_month",
    metric: str = "revenue",
    top_n: int = 10,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze product performance metrics and rankings.

    Args:
        time_period: Analysis period
        metric: Performance metric (revenue, quantity_sold, profit_margin)
        top_n: Number of top/bottom performers to return
        category: Filter by product category

    Returns:
        Product performance rankings and insights
    """
    # Implementation analyzes sales and inventory data
    pass
```

### Comparison Tool

```python
@tool
def compare_periods(
    current_period: str,
    comparison_period: str,
    metric: str = "revenue",
    product_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compare metrics between different time periods.

    Args:
        current_period: Current analysis period
        comparison_period: Period to compare against
        metric: Metric to compare (revenue, sales_volume, etc.)
        product_id: Specific product comparison

    Returns:
        Comparison data with percentage changes and insights
    """
    # Implementation compares metrics across periods
    pass
```

### Chart Data Tool

```python
@tool
def generate_chart_data(
    chart_type: str,
    data_source: str,
    time_period: str = "last_month",
    product_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate data formatted for chart visualization.

    Args:
        chart_type: Type of chart (line, bar, pie, trend)
        data_source: Data to chart (sales, inventory, forecasts)
        time_period: Time range for data
        product_filter: Filter by product or category

    Returns:
        Chart-ready data with labels, values, and formatting
    """
    # Implementation formats data for frontend charts
    pass
```

### Stock Update Tool

```python
@tool
def update_stock(
    product_id: str,
    qty: float,
    unit: str,
    tx_type: str = "purchase",
    reason: str = "Updated via chat assistant"
) -> Dict[str, Any]:
    """
    Update inventory stock levels (basic inventory management).

    Args:
        product_id: Product to update
        qty: Quantity to add/adjust
        unit: Unit of measurement
        tx_type: Transaction type
        reason: Reason for update

    Returns:
        Updated inventory data and transaction confirmation
    """
    url = f"{BASE_URL}/api/v1/stock/update-stock"
    headers = {
        "X-Tenant-ID": X_TENANT_ID,
        "Content-Type": "application/json"
    }

    body = {
        "product_id": product_id,
        "qty": qty,
        "unit": unit,
        "tx_type": tx_type,
        "reason": reason
    }

    response = requests.post(url, headers=headers, json=body)
    return response.json()
```

---

## Prompting Rules for OpenAI/LLM Node

### System Instruction (Exact Text):

```
You are a sales analytics and forecasting assistant for Kochi Burger Junction. You help analyze sales trends, predict future performance, and provide data-driven insights. Use the provided tools to query sales data, inventory levels, and generate forecasts. Be conversational like ChatGPT but focus on actionable business insights. Present data clearly with key metrics, trends, and recommendations. If you need specific data, use the available tools. Keep responses engaging but under 400 words. Use emojis sparingly for key insights (📈 📉 💡 ⚠️).
```

### Context Structure for Each LLM Call:

```typescript
const context = {
  user_message: "Show me sales trends for Kerala Burger last month",
  extracted_slots: {
    intent: "analyze_sales_trends",
    product_name: "Kerala Burger",
    time_period: "last_month",
    metric_type: "revenue",
  },
  session_history: [
    { role: "user", content: "What are our best selling items?" },
    {
      role: "assistant",
      content: "📈 Top performers this month: Kerala Burger (₹45,000), Chicken Burger (₹32,000)...",
    },
    { role: "user", content: "Show me sales trends for Kerala Burger last month" },
  ],
  tool_results: {
    sales_data: {
      product_name: "Kerala Burger",
      total_revenue: 45000,
      total_quantity: 150,
      daily_trends: [...],
      growth_rate: 15.2,
      top_selling_days: [...]
    },
    inventory_data: {
      current_stock: "sufficient",
      projected_needs: "25kg ground beef, 150 buns"
    }
  },
};
```

### Response Guidelines:

- **Max length**: 400 words (longer for complex analytics)
- **Tone**: Conversational like ChatGPT, but business-focused
- **Data presentation**: Lead with key insights, then supporting metrics
- **Charts & Visuals**: Describe trends and suggest chart types when relevant
- **Actionable insights**: Always include business recommendations
- **UUID handling**: Hide raw UUIDs, use friendly product names
- **Error communication**: Use exact tool error messages when available
- **Emoji usage**: Sparingly for key insights (📈 growth, 📉 decline, 💡 insights, ⚠️ warnings)

---

## Slot-filling & Conversation Patterns

### Example Conversation Flows:

#### 1. Sales Trend Analysis

```
User: "How are our burger sales trending this month?"
Intent: analyze_sales_trends
Slots: { product_category: "menu", time_period: "this_month", metric_type: "revenue" }
Tool Call: analyze_sales_data(time_period="this_month", category="menu")
Response: "📈 Great news! Burger sales are up 15% this month (₹78,000 vs ₹68,000 last month). Kerala Burger leads with ₹32,000 revenue. Peak sales on weekends. Would you like me to forecast next month's performance?"
```

#### 2. Sales Forecasting

```
User: "Predict Kerala Burger sales for next month"
Intent: forecast_sales
Slots: { product_name: "Kerala Burger", forecast_days: 30 }
Tool Call: forecast_sales(product_id="resolved_id", forecast_days=30)
Response: "🔮 Based on current trends, I predict Kerala Burger will generate ₹38,000-42,000 next month (90% confidence). This is a 15-20% increase from current month. You'll need approximately 200 burger buns and 30kg ground beef."
```

#### 3. Product Performance Comparison

```
User: "Which menu items are our best sellers vs worst performers?"
Intent: analyze_product_performance
Slots: { metric: "revenue", category: "menu", top_n: 5 }
Tool Call: analyze_product_performance(metric="revenue", category="menu", top_n=5)
Response: "🏆 Top Performers: 1) Kerala Burger (₹32k), 2) Chicken Burger (₹28k), 3) Fish Burger (₹18k). 📉 Underperformers: Seafood Combo (₹3k), Classic Combo (₹5k). Consider promoting underperformers or reviewing pricing."
```

#### 4. Inventory Impact Analysis

```
User: "What inventory should I prioritize based on sales forecasts?"
Intent: view_inventory_status + forecast_sales
Slots: { analysis_type: "inventory_planning" }
Tool Calls: get_inventory_status(), forecast_sales(forecast_days=14)
Response: "💡 Priority inventory: Ground beef (current: 8kg, need 25kg for forecasted sales), Burger buns (low stock, need 200pcs). Tomatoes expiring soon - use in promotions. Chicken stock is sufficient for 2 weeks."
```

#### 5. Period Comparison

```
User: "Compare this month's revenue to last month"
Intent: compare_periods
Slots: { current_period: "this_month", comparison_period: "last_month", metric: "revenue" }
Tool Call: compare_periods(current_period="this_month", comparison_period="last_month")
Response: "📊 Month-over-month comparison: Revenue up 12% (₹85,000 vs ₹76,000). Menu items grew 18%, raw material costs increased 8%. Net profit margin improved from 22% to 25%. Kerala Burger drove most growth (+₹8,000)."
```

#### 6. Follow-up Context with Data Continuity

```
User: "Show me Kerala Burger performance"
Bot: "📈 Kerala Burger: ₹32,000 revenue this month, 107 units sold, 15% growth rate..."
User: "What about next month's forecast for that?"
Context: last_analyzed_product = "Kerala Burger" (product_id + performance data cached)
Intent: forecast_sales
Tool Call: forecast_sales(product_id="cached_id", forecast_days=30)
Response: "🔮 Kerala Burger forecast for next month: ₹38,000-42,000 revenue (120-140 units). Growth momentum continues!"
```

---

## Normalization & Reply Rules

### Sales Data Presentation:

```
Format: "📈 {product_name}: ₹{revenue} revenue, {quantity} units sold ({growth}% vs previous period)"
Insights: Always include growth rates, comparisons, and trends
Example: "📈 Kerala Burger: ₹32,000 revenue, 107 units sold (+15% vs last month). Peak sales on weekends."
```

### Forecasting Results:

```
Format: "🔮 {product_name} forecast ({period}): ₹{min_revenue}-{max_revenue} ({confidence}% confidence)"
Additional: Include inventory implications
Example: "🔮 Kerala Burger forecast (next month): ₹38,000-42,000 (90% confidence). You'll need 200 buns, 30kg beef."
```

### Performance Rankings:

```
Format: "🏆 Top Performers: 1) {product} (₹{amount}), 2) {product} (₹{amount})..."
Include insights: Growth rates, trends, recommendations
Example: "🏆 Top Performers: 1) Kerala Burger (₹32k, +15%), 2) Chicken Burger (₹28k, +8%). Kerala Burger shows strongest momentum."
```

### Inventory Status with Sales Context:

```
Format: "{name}: {qty} {unit} ({stock_status}) - {sales_velocity} sales velocity"
Recommendation: Connect inventory to sales patterns
Example: "Tomatoes: 20kg (expiring_soon) - High velocity item. Consider using in promotions before expiry."
```

### Period Comparisons:

```
Format: "📊 {current} vs {previous}: {metric} {change}% ({current_value} vs {previous_value})"
Insights: Explain drivers of change
Example: "📊 This month vs last: Revenue +12% (₹85k vs ₹76k). Kerala Burger drove most growth (+₹8k)."
```

### Chart Data Descriptions:

```
Format: "📊 [Chart Type] showing {data_description}"
Include: Key insights and trends visible in the data
Example: "📊 Line chart shows daily revenue trends - steady growth with weekend peaks. Recommend weekend staff optimization."
```

---

## Node/TypeScript Minimal Server

### Package Dependencies:

```json
{
  "dependencies": {
    "express": "^4.18.2",
    "@types/express": "^4.17.17",
    "multer": "^1.4.5-lts.1",
    "@types/multer": "^1.4.7",
    "cors": "^2.8.5",
    "@types/cors": "^2.8.13",
    "openai": "^4.20.1",
    "dotenv": "^16.3.1",
    "typescript": "^5.2.2",
    "ts-node": "^10.9.1",
    "@langchain/langgraph": "^0.0.20",
    "express-rate-limit": "^7.1.5",
    "helmet": "^7.1.0",
    "ioredis": "^5.3.2",
    "chart.js": "^4.4.0",
    "date-fns": "^2.30.0",
    "uuid": "^9.0.1",
    "@types/uuid": "^9.0.7"
  }
}
```

### ChatGPT-like Server Implementation:

```typescript
import express from "express";
import multer from "multer";
import cors from "cors";
import helmet from "helmet";
import rateLimit from "express-rate-limit";
import { OpenAI } from "openai";
import { v4 as uuidv4 } from "uuid";
import dotenv from "dotenv";

dotenv.config();

const app = express();
const upload = multer({
  dest: "uploads/",
  limits: { fileSize: 10 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const allowedTypes = ["image/jpeg", "image/png", "image/webp"];
    cb(null, allowedTypes.includes(file.mimetype));
  },
});

// Enhanced session store for analytics context
interface AnalyticsSession {
  id: string;
  messages: Array<{
    role: string;
    content: string;
    timestamp: number;
    metadata?: {
      intent?: string;
      toolsUsed?: string[];
      dataContext?: any;
    };
  }>;
  lastAnalyzedProduct?: {
    id: string;
    name: string;
    type: string;
    lastMetrics?: any;
  };
  lastTimeframe?: string;
  conversationContext?: {
    currentAnalysisType?: string;
    pendingComparisons?: any[];
    chartPreferences?: any;
  };
  createdAt: number;
  lastUpdated: number;
}

const sessions = new Map<string, AnalyticsSession>();
const SESSION_TTL = parseInt(process.env.SESSION_TTL_SECONDS || "3600") * 1000;

// OpenAI client with function calling
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Rate limiting
const chatRateLimit = rateLimit({
  windowMs: 1 * 60 * 1000,
  max: 50,
  message: "Too many requests, please try again later",
});

// Security middleware
app.use(helmet());
app.use(
  cors({
    origin: process.env.CORS_ORIGIN || "http://localhost:3001",
    credentials: true,
  })
);

// Session management for analytics context
function getSession(sessionId: string): AnalyticsSession {
  const session = sessions.get(sessionId);
  if (!session || Date.now() - session.lastUpdated > SESSION_TTL) {
    const newSession: AnalyticsSession = {
      id: sessionId,
      messages: [],
      createdAt: Date.now(),
      lastUpdated: Date.now(),
    };
    sessions.set(sessionId, newSession);
    return newSession;
  }
  return session;
}

function updateSession(
  sessionId: string,
  role: string,
  content: string,
  metadata?: any
) {
  const session = getSession(sessionId);
  session.messages.push({
    role,
    content,
    timestamp: Date.now(),
    metadata,
  });

  // Keep last 20 messages for better context
  session.messages = session.messages.slice(-20);
  session.lastUpdated = Date.now();
}

// LangGraph flow with tools integration
async function executeLangGraphFlow(input: any) {
  // Load and execute LangGraph flow with tool calling
  // const flow = await loadCompiledGraph('./langgraph/sales_analytics_flow.json');
  // return await flow.execute(input);

  // Placeholder for development
  return {
    response:
      "I can help you analyze sales data and forecast trends. What would you like to explore?",
    toolsUsed: [],
    extractedData: null,
  };
}

// Main chat endpoint with streaming support
app.post("/chat", chatRateLimit, upload.single("image"), async (req, res) => {
  try {
    const { message, session_id = uuidv4(), stream = false } = req.body;
    const imageFile = req.file;

    // Get session context
    const session = getSession(session_id);

    // Prepare input for LangGraph flow
    const flowInput = {
      message,
      session_id,
      image: imageFile?.path,
      context: {
        conversationHistory: session.messages.slice(-10),
        lastAnalyzedProduct: session.lastAnalyzedProduct,
        lastTimeframe: session.lastTimeframe,
        conversationContext: session.conversationContext,
      },
    };

    if (stream && process.env.ENABLE_STREAMING === "true") {
      // Set up streaming response
      res.setHeader("Content-Type", "text/event-stream");
      res.setHeader("Cache-Control", "no-cache");
      res.setHeader("Connection", "keep-alive");

      // Execute LangGraph flow with streaming
      const flowResult = await executeLangGraphFlow(flowInput);

      // Stream response chunks
      const responseChunks = flowResult.response.split(" ");
      for (const chunk of responseChunks) {
        res.write(`data: ${JSON.stringify({ chunk, done: false })}\n\n`);
        await new Promise((resolve) => setTimeout(resolve, 50)); // Simulate typing
      }

      res.write(`data: ${JSON.stringify({ done: true, session_id })}\n\n`);
      res.end();
    } else {
      // Regular response
      const flowResult = await executeLangGraphFlow(flowInput);

      // Update session with metadata
      updateSession(session_id, "user", message);
      updateSession(session_id, "assistant", flowResult.response, {
        intent: flowResult.intent,
        toolsUsed: flowResult.toolsUsed,
        dataContext: flowResult.extractedData,
      });

      res.json({
        message: flowResult.response,
        session_id,
        metadata: {
          toolsUsed: flowResult.toolsUsed,
          hasChartData: flowResult.hasChartData,
        },
      });
    }
  } catch (error) {
    console.error("Chat error:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

// Get conversation history
app.get("/chat/:session_id/history", (req, res) => {
  const session = sessions.get(req.params.session_id);
  if (!session) {
    return res.status(404).json({ error: "Session not found" });
  }

  res.json({
    messages: session.messages,
    context: {
      lastAnalyzedProduct: session.lastAnalyzedProduct,
      conversationContext: session.conversationContext,
    },
  });
});

// Health check
app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    timestamp: new Date().toISOString(),
    activeSessions: sessions.size,
  });
});

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Sales Analytics Assistant Server running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
});
```

### OpenAI Function Calling Integration:

```typescript
// Tool definitions for OpenAI function calling
const salesAnalyticsTools = [
  {
    type: "function",
    function: {
      name: "analyze_sales_data",
      description:
        "Analyze sales trends and patterns for specific time periods and products",
      parameters: {
        type: "object",
        properties: {
          time_period: {
            type: "string",
            enum: ["last_week", "last_month", "last_quarter"],
          },
          product_id: { type: "string" },
          category: { type: "string" },
          group_by: { type: "string", enum: ["day", "week", "month"] },
        },
      },
    },
  },
  {
    type: "function",
    function: {
      name: "forecast_sales",
      description: "Generate sales forecasts based on historical data",
      parameters: {
        type: "object",
        properties: {
          product_id: { type: "string" },
          forecast_days: { type: "number", enum: [7, 30, 90] },
          include_confidence: { type: "boolean" },
        },
      },
    },
  },
  {
    type: "function",
    function: {
      name: "get_inventory_status",
      description: "Get current inventory levels and stock status",
      parameters: {
        type: "object",
        properties: {
          filter_status: {
            type: "string",
            enum: ["low_stock", "out_of_stock", "expiring_soon"],
          },
          product_id: { type: "string" },
        },
      },
    },
  },
];

async function generateResponseWithTools(context: any): Promise<any> {
  const systemPrompt = `You are a sales analytics and forecasting assistant for Kochi Burger Junction. You help analyze sales trends, predict future performance, and provide data-driven insights. Use the provided tools to query sales data, inventory levels, and generate forecasts. Be conversational like ChatGPT but focus on actionable business insights. Present data clearly with key metrics, trends, and recommendations. If you need specific data, use the available tools. Keep responses engaging but under 400 words. Use emojis sparingly for key insights (📈 📉 💡 ⚠️).`;

  const messages = [
    { role: "system", content: systemPrompt },
    ...context.session_history,
    { role: "user", content: context.user_message },
  ];

  const response = await openai.chat.completions.create({
    model: process.env.OPENAI_MODEL || "gpt-4o-mini",
    messages,
    tools: salesAnalyticsTools,
    tool_choice: "auto",
    max_tokens: 800,
    temperature: 0.7,
  });

  return response;
}
```

---

## Test Harness & Sample Utterances

### Automated Test Scenarios:

#### Test 1: Sales Trends Analysis

```bash
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me sales trends for last month",
    "session_id": "test_session_1"
  }'
```

**Expected**: Response includes sales metrics, growth rates, top performers, and trend insights with emojis.

#### Test 2: Product Performance Analysis

```bash
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Which menu items are performing best this quarter?",
    "session_id": "test_session_2"
  }'
```

**Expected**: Response shows ranked product performance with revenue figures and growth percentages.

#### Test 3: Sales Forecasting

```bash
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Predict Kerala Burger sales for next 30 days",
    "session_id": "test_session_3"
  }'
```

**Expected**: Response provides forecast range with confidence levels and inventory implications.

#### Test 4: Period Comparison

```bash
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Compare this month revenue vs last month",
    "session_id": "test_session_4"
  }'
```

**Expected**: Response shows percentage changes, absolute values, and identifies key growth drivers.

#### Test 5: Streaming Response

```bash
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze inventory levels and give me insights",
    "session_id": "test_session_5",
    "stream": true
  }'
```

**Expected**: Server-sent events stream with typing simulation and comprehensive inventory analysis.

#### Test 6: Follow-up Context

```bash
# First message
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me Kerala Burger performance",
    "session_id": "test_session_6"
  }'

# Follow-up message
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What about the forecast for that product?",
    "session_id": "test_session_6"
  }'
```

**Expected**: Second response uses context from first message to forecast the previously analyzed product.

### Test Assertions:

1. **Sales trends**: Response includes revenue figures, growth percentages, and trend insights
2. **Product performance**: Response shows ranked products with metrics and actionable recommendations
3. **Forecasting**: Response provides forecast ranges, confidence levels, and inventory implications
4. **Period comparison**: Response shows percentage changes, absolute values, and growth drivers
5. **Streaming**: Response arrives as server-sent events with proper formatting
6. **Follow-up context**: Second response uses data context from previous product analysis

---

## Error Handling & Validation Strategy

### Tool Error Handling in LangGraph:

```typescript
async function handleInventoryAPICall(endpoint: string, options: RequestInit) {
  try {
    const response = await callInventoryAPI(endpoint, options);
    const data = await response.json();

    if (!response.ok) {
      // 4xx Validation Errors
      if (response.status >= 400 && response.status < 500) {
        return {
          error: true,
          message: data.errors?.message || "Validation error",
          type: "validation",
          suggestion: generateSuggestion(data.errors?.message),
        };
      }

      // 5xx Server Errors
      return {
        error: true,
        message: "Server temporarily unavailable. Please try again.",
        type: "server_error",
      };
    }

    return { error: false, data };
  } catch (networkError) {
    return {
      error: true,
      message:
        "Unable to connect to inventory system. Please check your connection and try again.",
      type: "network_error",
    };
  }
}
```

### Product Name Resolution:

```typescript
function findProductMatches(name: string, inventory: any[]): any[] {
  const exactMatch = inventory.filter(
    (item) => item.name.toLowerCase() === name.toLowerCase()
  );

  if (exactMatch.length === 1) return exactMatch;

  const partialMatches = inventory.filter(
    (item) =>
      item.name.toLowerCase().includes(name.toLowerCase()) ||
      name.toLowerCase().includes(item.name.toLowerCase())
  );

  return partialMatches.slice(0, 3); // Return top 3 matches
}
```

### Response Normalization:

```typescript
function normalizeAPIResponse(apiResult: any, intent: string) {
  switch (intent) {
    case "view_inventory_list":
      return {
        items:
          apiResult.inventory_items?.map((item) => ({
            name: item.name,
            available_qty: item.available_qty,
            unit: item.unit,
            stock_status: item.stock_status,
            earliest_expiry_date: item.earliest_expiry_date,
          })) || [],
        summary: apiResult.summary,
      };

    case "update_stock_single":
      return {
        updated_items: apiResult.data?.[0]?.updated_items || [],
        transaction_ids: apiResult.data?.[0]?.transaction_ids || [],
      };

    default:
      return apiResult;
  }
}
```

---

## Session Management & Follow-ups

### Session Structure:

```typescript
interface SessionData {
  messages: Array<{
    role: "user" | "assistant";
    content: string;
    timestamp: number;
    metadata?: {
      intent?: string;
      extractedSlots?: any;
      apiCall?: string;
    };
  }>;
  lastSelectedProduct?: {
    id: string;
    name: string;
    type: string;
  };
  lastInventorySnapshot?: any[]; // For "show me more" queries
  preferences?: {
    defaultUnit?: string;
    defaultTxType?: string;
  };
  createdAt: number;
  lastUpdated: number;
}
```

### Follow-up Resolution:

```typescript
function resolveFollowupContext(message: string, session: SessionData) {
  const followupPatterns = [
    /add (\d+\.?\d*)\s*(\w+)?\s*to (that|it)/i,
    /update (that|it) with/i,
    /(that|it|same) (one|item|product)/i,
  ];

  if (followupPatterns.some((pattern) => pattern.test(message))) {
    if (session.lastSelectedProduct) {
      return {
        isFollowup: true,
        productId: session.lastSelectedProduct.id,
        productName: session.lastSelectedProduct.name,
      };
    }
  }

  return { isFollowup: false };
}
```

### TTL and Cleanup:

```typescript
// Cleanup expired sessions every 5 minutes
setInterval(() => {
  const now = Date.now();
  for (const [sessionId, session] of sessions.entries()) {
    if (now - session.lastUpdated > SESSION_TTL) {
      sessions.delete(sessionId);
    }
  }
}, 5 * 60 * 1000);
```

---

## Security & Operational Considerations

### File Upload Security:

```typescript
const secureUpload = multer({
  dest: "uploads/",
  limits: {
    fileSize: 10 * 1024 * 1024, // 10MB max
    files: 1,
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = ["image/jpeg", "image/png", "image/webp"];
    if (allowedTypes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error("Only JPEG, PNG, and WebP images allowed"));
    }
  },
});
```

### Rate Limiting:

```typescript
import rateLimit from "express-rate-limit";

const chatRateLimit = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 30, // 30 requests per minute per IP
  message: "Too many chat requests, please try again later",
});

const openaiRateLimit = rateLimit({
  windowMs: 1 * 60 * 1000,
  max: 20, // 20 OpenAI calls per minute
  keyGenerator: (req) => req.body.session_id || req.ip,
});
```

### Security Headers & CORS:

```typescript
app.use(
  cors({
    origin: process.env.FRONTEND_URL || "http://localhost:3001",
    credentials: true,
  })
);

app.use((req, res, next) => {
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.setHeader("X-Frame-Options", "DENY");
  res.setHeader("X-XSS-Protection", "1; mode=block");
  next();
});
```

### Logging & Monitoring:

```typescript
// Never log API keys or sensitive data
function sanitizeForLogging(data: any) {
  const sanitized = { ...data };
  delete sanitized.apiKey;
  delete sanitized.session_id;
  if (sanitized.headers) delete sanitized.headers["X-Tenant-ID"];
  return sanitized;
}

// Audit log for stock updates
function auditStockUpdate(
  sessionId: string,
  productId: string,
  qty: number,
  txType: string
) {
  console.log(
    `AUDIT: Session ${sessionId.slice(0, 8)} updated ${productId.slice(
      0,
      8
    )} qty=${qty} type=${txType} at ${new Date().toISOString()}`
  );
}
```

---

## Acceptance Criteria

### Functional Requirements:

1. **ChatGPT-like Conversation**: Users can ask natural language questions about sales and receive engaging, analytical responses
2. **Sales Analytics**:
   - Analyze sales trends, revenue patterns, and growth rates
   - Compare performance across different time periods
   - Identify top and bottom performing products
   - Provide actionable business insights with recommendations
3. **Sales Forecasting**:
   - Predict future sales based on historical data and trends
   - Generate confidence intervals for forecasts
   - Connect forecasts to inventory planning needs
   - Support different forecasting periods (7, 30, 90 days)
4. **Inventory Intelligence**:
   - View current stock levels with sales velocity context
   - Connect inventory status to sales performance
   - Provide data-driven restocking recommendations
   - Alert on expiring items with sales implications
5. **Data Visualization Support**:
   - Generate chart-ready data for frontend visualization
   - Describe trends and patterns in conversational format
   - Support multiple chart types (line, bar, pie, trend)
6. **Enhanced Session Context**:
   - Remember last 20 interactions with rich metadata
   - Track analyzed products and time periods
   - Handle complex follow-up questions with data continuity
   - 60-minute session TTL with analytics context preservation

### Technical Requirements:

1. **LangGraph Export**: Complete flow definition with tool-based database access
2. **ChatGPT-like Server**: Express server with streaming support and rich session management
3. **OpenAI Function Calling**: Integration with tool definitions for sales analytics
4. **Database Tools**: All queries implemented as LangGraph tools (no direct API calls in nodes)
5. **Error Handling**: Graceful handling of tool errors, data validation, and network issues
6. **Security & Performance**: Rate limiting, streaming, session cleanup, and audit logging
7. **Testing**: 6 automated test scenarios including streaming and follow-up context

### Behavior Expectations:

- **"Show me sales trends"** → Analyzes data using tools, returns insights with growth rates and emojis
- **"Predict next month's sales"** → Uses forecasting tools, provides confidence ranges and inventory implications
- **"Which products sell best?"** → Ranks products by performance metrics with actionable recommendations
- **"Compare this month vs last"** → Uses comparison tools, shows percentage changes and drivers
- **Follow-up "What about forecasts for that?"** → Uses cached product context from previous analysis
- **Streaming responses** → Simulates typing with server-sent events for better UX

---

## Future Improvements

### Optional Enhancements (Not in MVP):

- **Redis Session Backend**: Replace in-memory sessions for production scalability
- **Advanced ML Models**: Custom forecasting models beyond simple trend analysis
- **Real-time Dashboard**: Live updating charts and metrics integration
- **Export Capabilities**: PDF reports, Excel exports, and scheduled reports
- **Role-based Analytics**: Different insights for Admin/Manager/Chef/Staff users
- **Voice Analytics**: Speech-to-text for hands-free data queries
- **Mobile Optimization**: Progressive Web App with offline capabilities
- **Advanced Visualizations**: Interactive charts, heatmaps, and correlation analysis
- **Alert System**: Proactive notifications for trends and anomalies
- **Integration APIs**: Connect with POS systems, accounting software, and business intelligence tools

### Performance Optimizations:

- **Analytics Caching**: Cache sales data queries for 5-10 minutes
- **Connection Pooling**: HTTP client optimization for database tools
- **Batch Tool Calls**: Combine multiple analytics queries when possible
- **Streaming Responses**: Real-time response delivery for better UX
- **Session Compression**: Optimize conversation history storage
- **Chart Data Caching**: Cache visualization data with smart invalidation

---

## Repository Layout

```
iims-agent/
├── README.md
├── package.json
├── tsconfig.json
├── .env.example
├── .gitignore
├── langgraph/
│   ├── flows/
│   │   ├── sales_analytics_flow.py
│   │   ├── forecasting_flow.py
│   │   └── conversation_flow.py
│   ├── tools/
│   │   ├── sales_analytics_tool.py
│   │   ├── forecasting_tool.py
│   │   ├── inventory_tool.py
│   │   ├── comparison_tool.py
│   │   └── chart_data_tool.py
│   ├── nodes/
│   │   ├── intent_extraction.py
│   │   ├── slot_filling.py
│   │   ├── tool_orchestration.py
│   │   ├── response_generation.py
│   │   └── session_management.py
│   ├── config/
│   │   └── analytics_config.yaml
│   └── compiled/
│       └── sales_assistant_flow.json
├── server/
│   ├── src/
│   │   ├── index.ts
│   │   ├── routes/
│   │   │   ├── chat.ts
│   │   │   └── analytics.ts
│   │   ├── services/
│   │   │   ├── openai.ts
│   │   │   ├── langgraph_client.ts
│   │   │   ├── session_store.ts
│   │   │   └── analytics_cache.ts
│   │   ├── middleware/
│   │   │   ├── rate_limit.ts
│   │   │   ├── streaming.ts
│   │   │   └── validation.ts
│   │   └── utils/
│   │       ├── chart_helpers.ts
│   │       ├── date_utils.ts
│   │       └── response_formatter.ts
│   └── uploads/
├── tests/
│   ├── integration/
│   │   ├── sales_analytics.test.ts
│   │   ├── forecasting.test.ts
│   │   └── streaming_chat.test.ts
│   ├── unit/
│   │   ├── tool_integration.test.ts
│   │   ├── session_management.test.ts
│   │   └── analytics_helpers.test.ts
│   └── fixtures/
│       ├── sales_conversations.json
│       ├── mock_sales_data.json
│       └── test_chart_data.json
└── docs/
    ├── TOOLS_INTEGRATION.md
    ├── ANALYTICS_GUIDE.md
    └── DEPLOYMENT.md
```

---

## Implementation Instructions

This README provides a complete specification for implementing an MVP ChatGPT-like conversational assistant for sales analytics and forecasting. The implementation should be done in phases:

### Phase 1: LangGraph Tools Development

Create all database tools as LangGraph tools (sales_analytics_tool, forecasting_tool, inventory_tool, etc.) following the tool definitions above. Each tool should handle database queries and return structured data for analysis.

### Phase 2: LangGraph Flows & Orchestration

Build the conversation flows with tool orchestration nodes that can call multiple tools in sequence or parallel. Focus on natural conversation flow with proper intent classification for analytics queries.

### Phase 3: ChatGPT-like Server Interface

Implement the Express server with streaming support, enhanced session management for analytics context, and OpenAI function calling integration. Include all ChatGPT-like features (typing simulation, conversation history, rich context).

### Phase 4: Analytics & Visualization

Add chart data generation, trend analysis, and forecasting capabilities. Ensure responses are conversational but data-driven with actionable insights.

### Phase 5: Integration & Testing

Set up the 6 test scenarios focusing on sales analytics conversations. Validate streaming responses, follow-up context, and tool-based data access.

**Implementation Note**: When ready to implement, ask Cursor to create each component following this specification. Request both a LangGraph export file with all tools defined and a complete zipped repository with ChatGPT-like interface.

### Key Constraints Reminder:

- **NO RAG, NO VECTOR DB** - All context is session-based only with rich analytics metadata
- **Tool-based Database Access** - All data queries must be LangGraph tools, not direct API calls in flows
- **ChatGPT-like UX** - Conversational, engaging responses with streaming support
- **Analytics Focus** - Primary use case is sales analysis and forecasting, not general inventory management
- **Security & Performance** - Implement streaming, caching, and rate limiting from day one

This README serves as the complete specification for a ChatGPT-like sales analytics assistant. Follow each section precisely to ensure a working MVP that provides engaging, data-driven conversations about sales performance and forecasting.
