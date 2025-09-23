# Tools Integration Guide

This document explains how the LangGraph tools integrate with the backend API and OpenAI function calling.

## 🛠️ Tool Architecture

### Tool-Based Database Access

All database queries are implemented as LangGraph tools following the README specification:

```
User Message → Intent Classification → Tool Selection → API Calls → Response Generation
```

**Key Principle**: No direct API calls in LangGraph flows - everything goes through tools.

## 📊 Available Tools

### 1. Sales Analytics Tool (`sales_analytics_tool.py`)

**Purpose**: Analyze sales trends, patterns, and performance metrics

**Functions**:
- `analyze_sales_data()` - Main sales analysis with filters
- `get_product_sales_velocity()` - Product-specific performance metrics

**API Integration**:
```python
# Uses GET /api/v1/inventory as proxy for sales data
# In production, would call dedicated sales analytics endpoints
url = f"{BASE_URL}/api/v1/inventory"
headers = {"X-Tenant-ID": X_TENANT_ID, "Content-Type": "application/json"}
response = requests.get(url, headers=headers)
```

### 2. Forecasting Tool (`forecasting_tool.py`)

**Purpose**: Generate sales predictions and demand forecasting

**Functions**:
- `forecast_sales()` - Sales forecasting with confidence intervals
- `analyze_seasonal_trends()` - Seasonal pattern analysis

**Business Logic**:
- Uses historical patterns and growth factors
- Includes inventory planning implications
- Provides confidence levels and risk assessment

### 3. Inventory Tool (`inventory_tool.py`)

**Purpose**: Inventory status with sales context integration

**Functions**:
- `get_inventory_status()` - Enhanced inventory with sales velocity
- `check_stock_alerts()` - Critical inventory alerts with sales impact

**API Integration**:
```python
# Direct integration with inventory API per contract.md
url = f"{BASE_URL}/api/v1/inventory"
if product_id:
    url += f"/{product_id}"
response = requests.get(url, headers=headers)
```

### 4. Product Performance Tool (`product_performance_tool.py`)

**Purpose**: Dedicated product ranking and performance analysis

**Functions**:
- `analyze_product_performance()` - Product rankings with comparisons
- `get_product_ranking_by_category()` - Category-based performance analysis

### 5. Comparison Tool (`comparison_tool.py`)

**Purpose**: Period-to-period and metric comparisons

**Functions**:
- `compare_periods()` - Time period comparisons with growth analysis
- `analyze_growth_drivers()` - Growth factor identification

### 6. Chart Data Tool (`chart_data_tool.py`)

**Purpose**: Generate visualization-ready data

**Functions**:
- `generate_chart_data()` - Chart.js compatible data formats
- `create_dashboard_summary()` - Multi-chart dashboard data

### 7. Stock Update Tool (`stock_update_tool.py`)

**Purpose**: Basic inventory management operations

**Functions**:
- `update_stock()` - Single product stock updates
- `bulk_stock_update()` - Multiple product batch updates

**API Integration**:
```python
# Uses POST /api/v1/stock/update-stock per contract.md
url = f"{BASE_URL}/api/v1/stock/update-stock"
body = {
    "product_id": product_id,
    "qty": qty,
    "unit": unit,
    "tx_type": tx_type,
    "reason": reason
}
response = requests.post(url, headers=headers, json=body)
```

### 8. Report Generation Tool (`report_generation_tool.py`)

**Purpose**: Create structured reports and comprehensive summaries

**Functions**:
- `generate_sales_report()` - Comprehensive sales reports
- `create_performance_summary()` - Focused performance summaries

## 🔗 OpenAI Function Calling Integration

### Tool Definitions for OpenAI

The `src/services/openai_integration.ts` implements the exact tool schemas from the README:

```typescript
const salesAnalyticsTools = [
  {
    type: "function",
    function: {
      name: "analyze_sales_data",
      description: "Analyze sales trends and patterns for specific time periods and products",
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
  // ... other tools
];
```

### Function Calling Flow

1. **User Message** → OpenAI determines if tools are needed
2. **Tool Selection** → OpenAI chooses appropriate tools and parameters
3. **Tool Execution** → LangGraph executes the selected tools
4. **Result Integration** → Tool results fed back to OpenAI for response generation
5. **Final Response** → Conversational response with insights and recommendations

## 🔄 Tool Orchestration in LangGraph

### Main Flow (`sales_analytics_flow.py`)

```python
# Graph structure
workflow = StateGraph(AnalyticsState)

# Nodes
workflow.add_node("extract_intent", extract_intent_and_slots)
workflow.add_node("call_tools", route_to_tools)  
workflow.add_node("generate_response", generate_response)
workflow.add_node("update_context", update_session_context)

# Flow
START → extract_intent → call_tools → generate_response → update_context → END
```

### Tool Routing Logic

```python
def route_to_tools(state: AnalyticsState) -> AnalyticsState:
    intent = state["extracted_intent"]
    slots = state["extracted_slots"]
    
    if intent == "analyze_sales_trends":
        result = analyze_sales_data(
            time_period=slots.get("time_period", "last_month"),
            product_id=slots.get("product_id"),
            category=slots.get("category")
        )
    elif intent == "forecast_sales":
        result = forecast_sales(
            product_name=slots.get("product_name"),
            forecast_days=slots.get("forecast_days", 30)
        )
    # ... other tool routing
```

## 🧪 Testing Tool Integration

### Unit Tests

```bash
# Test individual tools
python -c "
import asyncio
from langgraph.tools.sales_analytics_tool import analyze_sales_data
result = asyncio.run(analyze_sales_data.ainvoke({'time_period': 'last_month'}))
print('Success:', result.get('success'))
"
```

### Integration Tests

```bash
# Test complete flow
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me sales trends for last month",
    "session_id": "test_integration"
  }'
```

## 🔒 Security Considerations

### API Security

- All tools use proper headers: `X-Tenant-ID`, `Content-Type`
- Request timeout and retry logic implemented
- Input validation and sanitization
- Error message sanitization (no sensitive data exposed)

### Tool Parameter Validation

```python
def validate_tool_params(params: Dict[str, Any]) -> Dict[str, Any]:
    # Validate time periods
    if "time_period" in params:
        valid_periods = ["last_week", "last_month", "last_quarter"]
        if params["time_period"] not in valid_periods:
            params["time_period"] = "last_month"  # Default
    
    # Validate forecast days
    if "forecast_days" in params:
        if params["forecast_days"] not in [7, 30, 90]:
            params["forecast_days"] = 30  # Default
            
    return params
```

## 📈 Performance Optimization

### Tool Caching (Future Enhancement)

```python
# Example caching strategy for production
@tool
@cache(ttl=300)  # 5-minute cache
def analyze_sales_data(...):
    # Tool implementation
    pass
```

### Parallel Tool Execution

```python
# Execute multiple tools in parallel when possible
async def execute_parallel_tools(tools_to_call):
    tasks = []
    for tool_call in tools_to_call:
        task = asyncio.create_task(tool_call["tool"].ainvoke(tool_call["args"]))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

## 🚨 Error Handling

### Tool Error Patterns

```python
# Standard error response format
{
    "error": True,
    "message": "User-friendly error message",
    "tool": "tool_name",
    "endpoint": "api_endpoint_called",
    "status_code": 400,  # If applicable
    "validation_error": True  # For 4xx errors
}
```

### Error Recovery

1. **API Unavailable** → Use cached data or mock responses
2. **Timeout** → Retry with exponential backoff
3. **Validation Error** → Request clarification from user
4. **Unknown Error** → Graceful fallback with helpful message

## 🔧 Troubleshooting

### Common Issues

**Tool imports failing**:
```bash
# Check Python path and virtual environment
source venv/bin/activate
python -c "from langgraph.tools.sales_analytics_tool import analyze_sales_data; print('✅ Import OK')"
```

**API connectivity issues**:
```bash
# Test direct API access
curl -H "X-Tenant-ID: 11111111-1111-1111-1111-111111111111" \
     http://localhost:8000/api/v1/inventory
```

**OpenAI function calling not working**:
- Verify `OPENAI_API_KEY` is set correctly
- Check tool schema format matches OpenAI requirements
- Ensure tool names match between LangGraph and OpenAI definitions

### Debug Mode

```python
# Enable debug logging for tools
import logging
logging.basicConfig(level=logging.DEBUG)

# Test tool execution with debug info
result = await analyze_sales_data.ainvoke({
    "time_period": "last_month",
    "debug": True
})
```

## 🎯 Production Deployment

### Tool Configuration

```yaml
# Production overrides in analytics_config.yaml
production:
  use_mock_data: false
  tool_timeout: 60  # Longer timeout for production
  enable_caching: true
  log_performance_metrics: true
```

### Monitoring

- Monitor tool execution times
- Track API call success rates
- Alert on tool failures or degraded performance
- Log tool usage patterns for optimization

## 🔄 Extending Tools

### Adding New Tools

1. Create tool file in `langgraph/tools/`
2. Define with `@tool` decorator
3. Add to imports in `sales_analytics_flow.py`
4. Add routing logic in `route_to_tools()`
5. Add OpenAI function definition in `openai_integration.ts`
6. Update configuration in `analytics_config.yaml`

### Example New Tool

```python
@tool
def analyze_customer_segments(
    segment_type: str = "behavior",
    time_period: str = "last_month"
) -> Dict[str, Any]:
    """
    Analyze customer segmentation and behavior patterns.
    """
    # Implementation here
    pass
```

This tools integration provides the foundation for the ChatGPT-like sales analytics assistant with proper separation of concerns and scalable architecture.
