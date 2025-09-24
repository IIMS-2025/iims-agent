"""
Pure ReAct (Reasoning and Acting) Analytics Flow for LangGraph
Implements true ReAct pattern where LLM autonomously decides which tools to call
"""

import os
import json
import re
from typing import Dict, Any, List, Optional, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from datetime import datetime

# Import all available tools - LLM will choose intelligently
from ..tools.sales_analytics_tool import analyze_sales_data, get_product_sales_velocity
from ..tools.forecasting_tool import forecast_sales, analyze_seasonal_trends
from ..tools.inventory_tool import get_inventory_status, check_stock_alerts
from ..tools.comparison_tool import compare_periods, analyze_growth_drivers
from ..tools.product_performance_tool import analyze_product_performance
from ..tools.chart_data_tool import generate_chart_data, create_dashboard_summary
from ..tools.report_generation_tool import generate_sales_report
from ..tools.backend_health_tool import check_backend_status, get_available_endpoints
from ..tools.cookbook_analysis_tool import get_all_cookbook_items, get_recipe_details, analyze_menu_profitability
from ..tools.wastage_analysis_tool import get_wastage_summary, analyze_wastage_by_product, track_wastage_trends
from ..tools.tenancy_management_tool import get_tenant_information, analyze_product_catalog, get_location_overview
from ..tools.batch_tracking_tool import get_batch_history, analyze_inventory_by_product, get_expiry_alerts

# ReAct State Definition
class ReActState(dict):
    """State for ReAct conversation flow"""
    user_message: str
    session_id: str
    conversation_history: List[Dict[str, Any]]
    
    # ReAct specific fields
    thought: str
    action: str
    action_input: Dict[str, Any]
    observation: str
    reasoning_history: List[Dict[str, Any]]
    
    # Final response
    final_response: str
    session_context: Dict[str, Any]
    
    # Control flow
    iteration_count: int
    max_iterations: int
    should_continue: bool

# Initialize LLM
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    temperature=0.3,  # Lower temperature for more consistent reasoning
    api_key=os.getenv("OPENAI_API_KEY")
)

# Available tools for ReAct
AVAILABLE_TOOLS = {
    # Inventory Management
    "get_inventory_status": get_inventory_status,
    "check_stock_alerts": check_stock_alerts,
    "analyze_inventory_by_product": analyze_inventory_by_product,
    "get_expiry_alerts": get_expiry_alerts,
    
    # Sales Analytics (Note: these return errors as no sales endpoints exist)
    "analyze_sales_data": analyze_sales_data,
    "get_product_sales_velocity": get_product_sales_velocity,
    "forecast_sales": forecast_sales,
    "analyze_seasonal_trends": analyze_seasonal_trends,
    "compare_periods": compare_periods,
    "analyze_growth_drivers": analyze_growth_drivers,
    "analyze_product_performance": analyze_product_performance,
    
    # Cookbook & Recipe Management
    "get_all_cookbook_items": get_all_cookbook_items,
    "get_recipe_details": get_recipe_details,
    "analyze_menu_profitability": analyze_menu_profitability,
    
    # Wastage Analysis
    "get_wastage_summary": get_wastage_summary,
    "analyze_wastage_by_product": analyze_wastage_by_product,
    "track_wastage_trends": track_wastage_trends,
    
    # Tenancy & Product Catalog
    "get_tenant_information": get_tenant_information,
    "analyze_product_catalog": analyze_product_catalog,
    "get_location_overview": get_location_overview,
    
    # Batch Tracking & Traceability
    "get_batch_history": get_batch_history,
    
    # Charts & Reports
    "generate_chart_data": generate_chart_data,
    "create_dashboard_summary": create_dashboard_summary,
    
    # System Health
    "check_backend_status": check_backend_status,
    "get_available_endpoints": get_available_endpoints
}

# Comprehensive tool documentation for LLM to make intelligent choices
TOOL_SCHEMAS = {
    # Inventory Management - PRIMARY WORKING TOOLS
    "get_inventory_status": {
        "description": "Get current inventory levels and stock status information with sales context",
        "parameters": {
            "filter_status": "str (low_stock, out_of_stock, expiring_soon, dead_stock)",
            "product_id": "str (specific product)",
            "include_batches": "bool (include batch details)",
            "include_sales_context": "bool (include sales velocity recommendations)"
        },
        "use_when": "User asks about stock levels, inventory status, what's in stock, stock alerts, current inventory"
    },
    "check_stock_alerts": {
        "description": "Check for inventory alerts that need immediate attention",
        "parameters": {
            "alert_types": "list (low_stock, expiring_soon, dead_stock)"
        },
        "use_when": "User asks about inventory problems, critical stock issues, urgent inventory matters, alerts"
    },
    "analyze_inventory_by_product": {
        "description": "Detailed inventory analysis for specific products including batch tracking",
        "parameters": {
            "product_id": "str (product ID to analyze - required)",
            "include_batch_details": "bool (include batch information)",
            "include_expiry_analysis": "bool (include expiry analysis)"
        },
        "use_when": "User asks about specific product inventory, batch details, product-specific stock analysis"
    },
    "get_expiry_alerts": {
        "description": "Get comprehensive expiry alerts across all inventory with prioritization",
        "parameters": {
            "days_ahead": "int (days to check ahead for expiring items)",
            "include_expired": "bool (include already expired items)",
            "severity_filter": "str (critical, warning, expired)"
        },
        "use_when": "User asks about expiring items, items going bad, expiry dates, waste prevention"
    },
    
    # Cookbook & Recipe Management - WORKING TOOLS
    "get_all_cookbook_items": {
        "description": "Get all cookbook items including recipes and menu analysis",
        "parameters": {
            "include_recipes": "bool (include recipe details)",
            "include_pricing": "bool (include pricing analysis)",
            "include_nutrition": "bool (include nutrition data)"
        },
        "use_when": "User asks about menu items, recipes, cookbook, what dishes are available, menu overview"
    },
    "get_recipe_details": {
        "description": "Get detailed recipe information for specific menu items",
        "parameters": {
            "product_id": "str (product ID for recipe - required)",
            "include_ingredient_analysis": "bool (detailed ingredient breakdown)",
            "include_cost_breakdown": "bool (cost analysis per ingredient)"
        },
        "use_when": "User asks about specific recipe, ingredients, how to make something, recipe details"
    },
    "analyze_menu_profitability": {
        "description": "Analyze menu profitability and pricing strategies",
        "parameters": {
            "category_filter": "str (filter by menu category)",
            "price_range": "str (low, medium, high price range filter)"
        },
        "use_when": "User asks about menu profitability, pricing strategy, most profitable items, menu analysis"
    },
    
    # Wastage Analysis - WORKING TOOLS
    "get_wastage_summary": {
        "description": "Get comprehensive wastage summary with trends and cost analysis",
        "parameters": {
            "days_back": "int (days to analyze)",
            "include_trends": "bool (include trend analysis)",
            "include_cost_analysis": "bool (include cost breakdowns)"
        },
        "use_when": "User asks about waste, wastage costs, food waste, loss analysis, waste trends"
    },
    "analyze_wastage_by_product": {
        "description": "Analyze wastage patterns for specific products or reasons",
        "parameters": {
            "product_id": "str (specific product to analyze)",
            "reason_filter": "str (expired, damaged, theft, other)",
            "days_back": "int (days to analyze)",
            "limit": "int (max records to return)"
        },
        "use_when": "User asks about waste for specific products, why items are wasted, wastage reasons"
    },
    "track_wastage_trends": {
        "description": "Track wastage trends over time for pattern identification",
        "parameters": {
            "time_period": "str (daily, weekly, monthly)",
            "months_back": "int (months of history to analyze)"
        },
        "use_when": "User asks about wastage trends over time, seasonal waste patterns, waste reduction progress"
    },
    
    # Tenancy & Product Catalog - WORKING TOOLS
    "get_tenant_information": {
        "description": "Get comprehensive tenant info including locations and products",
        "parameters": {
            "include_locations": "bool (include location details)",
            "include_products_summary": "bool (include product overview)"
        },
        "use_when": "User asks about business locations, tenant info, company overview, store locations"
    },
    "analyze_product_catalog": {
        "description": "Analyze product catalog structure and pricing",
        "parameters": {
            "tenant_id": "str (specific tenant)",
            "product_type": "str (raw_material, sub_product, menu_item)",
            "category": "str (product category filter)",
            "include_pricing_analysis": "bool (detailed pricing analysis)"
        },
        "use_when": "User asks about product catalog, product types, pricing analysis, product categories"
    },
    "get_location_overview": {
        "description": "Get overview of all business locations with operational insights",
        "parameters": {
            "tenant_id": "str (specific tenant)",
            "include_operational_metrics": "bool (operational analysis per location)"
        },
        "use_when": "User asks about business locations, store performance, location analysis, multi-location insights"
    },
    
    # Batch Tracking - WORKING TOOLS
    "get_batch_history": {
        "description": "Get comprehensive batch history for traceability and quality analysis",
        "parameters": {
            "batch_id": "str (specific batch ID to track - required)",
            "include_transactions": "bool (include transaction history)",
            "include_quality_metrics": "bool (include quality analysis)"
        },
        "use_when": "User asks about batch tracking, traceability, batch history, quality issues for specific batches"
    },
    
    # System Health - WORKING TOOLS
    "check_backend_status": {
        "description": "Check if the backend inventory API is available and responsive",
        "parameters": {},
        "use_when": "System errors, connectivity issues, or when other tools fail, backend problems"
    },
    "get_available_endpoints": {
        "description": "List all available API endpoints that can be used",
        "parameters": {},
        "use_when": "User asks about capabilities, available data, what can be analyzed, system capabilities"
    },
    
    # Sales Analytics - NOTE: THESE TOOLS RETURN ERRORS (no sales endpoints available)
    "analyze_sales_data": {
        "description": "Analyze sales trends and patterns - NOTE: Returns error, no sales endpoints",
        "parameters": {
            "time_period": "str (last_week, last_month, last_quarter)",
            "start_date": "str (ISO format for custom periods)",
            "end_date": "str (ISO format for custom periods)", 
            "product_id": "str (specific product UUID)",
            "category": "str (product category filter)",
            "group_by": "str (day, week, month)"
        },
        "use_when": "User asks about sales trends, patterns, performance over time, revenue analysis - BUT EXPECT ERRORS"
    },
    "get_product_sales_velocity": {
        "description": "Get sales velocity metrics - NOTE: Returns error, no sales endpoints",
        "parameters": {
            "product_name": "str (name of the product to analyze)"
        },
        "use_when": "User asks about specific product sales performance - BUT EXPECT ERRORS"
    },
    "forecast_sales": {
        "description": "Generate sales forecasts - NOTE: Returns error, no sales endpoints",
        "parameters": {
            "product_id": "str (specific product UUID)",
            "product_name": "str (product name to forecast)",
            "category": "str (product category)",
            "forecast_days": "int (7, 30, 90)",
            "include_confidence": "bool (include confidence intervals)",
            "include_inventory_impact": "bool (include inventory planning)"
        },
        "use_when": "User asks about predictions, forecasts, future sales - BUT EXPECT ERRORS"
    },
    "analyze_seasonal_trends": {
        "description": "Analyze seasonal trends - NOTE: Returns error, no sales endpoints",
        "parameters": {
            "product_category": "str (category to analyze)",
            "months_back": "int (months of history to analyze)"
        },
        "use_when": "User asks about seasonal patterns, cyclical trends - BUT EXPECT ERRORS"
    },
    "compare_periods": {
        "description": "Compare metrics between periods - NOTE: Returns error, no sales endpoints",
        "parameters": {
            "current_period": "str (this_week, this_month, this_quarter)",
            "comparison_period": "str (last_week, last_month, last_quarter)",
            "metric": "str (revenue, sales_volume, profit_margin)",
            "product_id": "str (specific product)",
            "category": "str (product category)"
        },
        "use_when": "User asks to compare periods, vs analysis, growth comparisons - BUT EXPECT ERRORS"
    },
    "analyze_growth_drivers": {
        "description": "Identify growth factors - NOTE: Returns error, no sales endpoints",
        "parameters": {
            "time_period": "str (analysis period)",
            "threshold": "float (minimum growth percentage)"
        },
        "use_when": "User asks what's driving growth, why sales increased/decreased - BUT EXPECT ERRORS"
    },
    "analyze_product_performance": {
        "description": "Analyze product performance - NOTE: Returns error, no sales endpoints",
        "parameters": {
            "time_period": "str (last_month, last_quarter)",
            "metric": "str (revenue, quantity_sold, profit_margin)",
            "top_n": "int (number of performers to return)",
            "category": "str (product category)",
            "include_comparisons": "bool (include period comparisons)"
        },
        "use_when": "User asks about product performance rankings - BUT EXPECT ERRORS"
    },
    "generate_chart_data": {
        "description": "Generate chart data - NOTE: Returns error, no sales endpoints",
        "parameters": {
            "chart_type": "str (line, bar, pie, trend)",
            "data_source": "str (sales, inventory, forecasts, performance)",
            "time_period": "str (time range for data)",
            "product_filter": "str (product/category filter)",
            "group_by": "str (aggregation level)"
        },
        "use_when": "User asks for charts, graphs, visualizations - BUT EXPECT ERRORS"
    },
    "create_dashboard_summary": {
        "description": "Create dashboard summary - NOTE: Returns error, no sales endpoints",
        "parameters": {
            "include_charts": "bool (include chart configurations)",
            "time_period": "str (period for dashboard data)"
        },
        "use_when": "User asks for dashboard, summary, overview - BUT EXPECT ERRORS"
    },
    "generate_sales_report": {
        "description": "Generate sales reports - NOTE: Returns error, no sales endpoints",
        "parameters": {
            "report_type": "str (comprehensive, summary, performance, trends)",
            "time_period": "str (last_week, last_month, last_quarter)",
            "include_forecasts": "bool (include forecast data)",
            "include_recommendations": "bool (include business recommendations)",
            "format_type": "str (summary, detailed, executive)"
        },
        "use_when": "User asks for reports, comprehensive analysis - BUT EXPECT ERRORS"
    }
}

def initialize_react_state(state: ReActState) -> ReActState:
    """Initialize ReAct state with default values"""
    state["reasoning_history"] = []
    state["iteration_count"] = 0
    state["max_iterations"] = 5
    state["should_continue"] = True
    state["thought"] = ""
    state["action"] = ""
    state["action_input"] = {}
    state["observation"] = ""
    return state

def react_reasoning_step(state: ReActState) -> ReActState:
    """
    ReAct Reasoning Step: Think about what to do next
    """
    
    user_message = state["user_message"]
    conversation_history = state.get("conversation_history", [])
    reasoning_history = state.get("reasoning_history", [])
    iteration_count = state.get("iteration_count", 0)
    
    # Build context for reasoning
    context = f"User Question: {user_message}\n\n"
    
    if reasoning_history:
        context += "Previous Reasoning Steps:\n"
        for i, step in enumerate(reasoning_history[-3:], 1):  # Last 3 steps
            context += f"Step {i}:\n"
            context += f"  Thought: {step.get('thought', '')}\n"
            context += f"  Action: {step.get('action', '')}\n"
            context += f"  Observation: {step.get('observation', '')}\n\n"
    
    # Create reasoning prompt with comprehensive tool information
    reasoning_prompt = f"""
    You are a sales analytics assistant using the ReAct (Reasoning and Acting) approach.
    You must INTELLIGENTLY choose which tools to call based on the user's question.
    
    {context}
    
    AVAILABLE TOOLS AND WHEN TO USE THEM:
    {json.dumps(TOOL_SCHEMAS, indent=2)}
    
    REACT METHODOLOGY:
    1. THINK: Analyze the user's question and determine what information you need
    2. ACT: Select the MOST APPROPRIATE tool and parameters for the current need
    3. OBSERVE: Review the tool result and determine next steps
    4. REPEAT: Continue until you have sufficient information for a complete answer
    
    INTELLIGENT TOOL SELECTION GUIDELINES:
    - Choose tools based on the user's specific question, not pre-defined patterns
    - Consider what information you already have vs what you still need
    - Start with broader analysis tools, then drill down to specifics if needed
    - If a tool fails, try a different approach or check system status
    - Don't call redundant tools - build on previous observations
    
    Current iteration: {iteration_count + 1} / 5
    
    CRITICAL REASONING STEPS:
    1. What EXACTLY is the user asking for?
    2. What data/analysis do I need to answer completely?
    3. What have I already learned from previous tool calls?
    4. What is the NEXT BEST tool to get closer to a complete answer?
    5. Do I have enough information now to provide a final answer?
    
    RESPONSE FORMAT (EXACTLY):
    Thought: [Your detailed reasoning about what tool to use and why]
    Action: [exact_tool_name OR "Final Answer"]  
    Action Input: {{"parameter_name": "value", "another_param": "value"}} OR N/A for Final Answer
    
    If you have sufficient information to fully answer the user's question:
    Action: Final Answer
    Action Input: N/A
    """
    
    try:
        response = llm.invoke([HumanMessage(content=reasoning_prompt)])
        result_text = response.content
        
        # Parse the ReAct format response
        thought_match = re.search(r'Thought:\s*(.*?)(?=Action:|$)', result_text, re.DOTALL)
        action_match = re.search(r'Action:\s*(.*?)(?=Action Input:|$)', result_text, re.DOTALL)
        action_input_match = re.search(r'Action Input:\s*(.*?)$', result_text, re.DOTALL)
        
        state["thought"] = thought_match.group(1).strip() if thought_match else "No clear thought provided"
        state["action"] = action_match.group(1).strip() if action_match else "Final Answer"
        
        # Parse action input
        if action_input_match:
            action_input_text = action_input_match.group(1).strip()
            if action_input_text.lower() in ["n/a", "none", ""]:
                state["action_input"] = {}
            else:
                try:
                    # Try to parse as JSON
                    json_match = re.search(r'\{.*\}', action_input_text, re.DOTALL)
                    if json_match:
                        state["action_input"] = json.loads(json_match.group())
                    else:
                        state["action_input"] = {}
                except json.JSONDecodeError:
                    state["action_input"] = {}
        else:
            state["action_input"] = {}
            
        # Determine if should continue
        state["should_continue"] = (
            state["action"] != "Final Answer" and 
            iteration_count < state.get("max_iterations", 5)
        )
        
        return state
        
    except Exception as e:
        state["thought"] = f"Error in reasoning: {str(e)}"
        state["action"] = "Final Answer"
        state["action_input"] = {}
        state["should_continue"] = False
        return state

async def react_action_step(state: ReActState) -> ReActState:
    """
    ReAct Action Step: Execute the chosen action
    """
    
    action = state.get("action", "")
    action_input = state.get("action_input", {})
    
    if action == "Final Answer":
        state["observation"] = "Ready to provide final answer"
        state["should_continue"] = False
        return state
    
    # Execute the tool
    if action in AVAILABLE_TOOLS:
        try:
            tool = AVAILABLE_TOOLS[action]
            
            # Call tool with parameters
            if action_input:
                result = await tool.ainvoke(action_input)
            else:
                result = await tool.ainvoke({})
                
            state["observation"] = json.dumps(result, indent=2)
            
        except Exception as e:
            state["observation"] = f"Error executing {action}: {str(e)}"
    else:
        state["observation"] = f"Unknown action: {action}. Available actions: {list(AVAILABLE_TOOLS.keys())}"
    
    # Add to reasoning history
    reasoning_step = {
        "iteration": state.get("iteration_count", 0) + 1,
        "thought": state.get("thought", ""),
        "action": action,
        "action_input": action_input,
        "observation": state["observation"],
        "timestamp": datetime.now().isoformat()
    }
    
    if "reasoning_history" not in state:
        state["reasoning_history"] = []
    state["reasoning_history"].append(reasoning_step)
    
    # Increment iteration count
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    
    return state

def should_continue_reasoning(state: ReActState) -> Literal["reasoning", "final_response"]:
    """
    Conditional edge: decide whether to continue reasoning or generate final response
    """
    return "reasoning" if state.get("should_continue", False) else "final_response"

def format_tool_results_for_response(reasoning_history: List[Dict[str, Any]]) -> str:
    """
    Universal tool result formatter - converts ANY tool output into readable business insights
    """
    formatted_insights = []
    
    for step in reasoning_history:
        tool_name = step.get('action', '')
        observation = step.get('observation', '')
        
        if observation and not observation.startswith("Error"):
            try:
                result_data = json.loads(observation)
                formatted_result = format_tool_output(tool_name, result_data)
                if formatted_result:
                    formatted_insights.append(formatted_result)
                    
            except json.JSONDecodeError:
                # Handle non-JSON observations
                formatted_insights.append(format_plain_text_output(tool_name, observation))
        else:
            # Handle errors
            formatted_insights.append(format_error_output(tool_name, observation))
    
    return "\n\n".join(formatted_insights)

def format_tool_output(tool_name: str, data: Dict[str, Any]) -> str:
    """
    Universal tool output formatter - routes to specific formatters or provides generic formatting
    """
    # Tool-specific formatters
    formatters = {
        # Inventory Management
        "get_inventory_status": format_inventory_insights,
        "check_stock_alerts": format_stock_alerts,
        "analyze_inventory_by_product": format_inventory_insights,
        "get_expiry_alerts": format_stock_alerts,
        
        # Cookbook & Recipe Management
        "get_all_cookbook_items": format_cookbook_insights,
        "get_recipe_details": format_recipe_insights,
        "analyze_menu_profitability": format_menu_insights,
        
        # Wastage Analysis
        "get_wastage_summary": format_wastage_insights,
        "analyze_wastage_by_product": format_wastage_insights,
        "track_wastage_trends": format_wastage_insights,
        
        # Tenancy & Product Catalog
        "get_tenant_information": format_tenant_insights,
        "analyze_product_catalog": format_catalog_insights,
        "get_location_overview": format_location_insights,
        
        # Batch Tracking
        "get_batch_history": format_batch_insights,
        
        # Sales Analytics (return errors)
        "analyze_sales_data": format_sales_insights,
        "forecast_sales": format_forecast_insights,
        "compare_periods": format_comparison_insights,
        "analyze_product_performance": format_performance_insights,
        "generate_chart_data": format_chart_insights,
        "create_dashboard_summary": format_dashboard_insights,
        "get_product_sales_velocity": format_velocity_insights,
        "analyze_growth_drivers": format_growth_insights,
        "analyze_seasonal_trends": format_seasonal_insights,
        "generate_sales_report": format_sales_insights,
        
        # System Health
        "check_backend_status": format_system_insights,
        "get_available_endpoints": format_endpoints_insights
    }
    
    # Use specific formatter if available
    if tool_name in formatters:
        return formatters[tool_name](data)
    
    # Generic formatter for unknown tools
    return format_generic_tool_output(tool_name, data)

def format_plain_text_output(tool_name: str, observation: str) -> str:
    """Format non-JSON tool outputs"""
    tool_display_name = tool_name.replace('_', ' ').title()
    if len(observation) > 300:
        return f"📊 **{tool_display_name}**: {observation[:300]}..."
    return f"📊 **{tool_display_name}**: {observation}"

def format_error_output(tool_name: str, observation: str) -> str:
    """Format error outputs"""
    tool_display_name = tool_name.replace('_', ' ').title()
    return f"⚠️ **{tool_display_name}**: {observation}"

def format_generic_tool_output(tool_name: str, data: Dict[str, Any]) -> str:
    """Generic formatter for any tool output"""
    tool_display_name = tool_name.replace('_', ' ').title()
    
    if not data.get('success', True):
        return f"⚠️ **{tool_display_name}**: {data.get('message', 'Operation failed')}"
    
    insights = [f"📊 **{tool_display_name.upper()}**"]
    
    # Extract key metrics
    key_fields = ['total', 'count', 'summary', 'result', 'data', 'value', 'score']
    for field in key_fields:
        if field in data and data[field] is not None:
            insights.append(f"• {field.title()}: {data[field]}")
    
    # Extract lists or arrays
    for key, value in data.items():
        if isinstance(value, list) and len(value) > 0:
            insights.append(f"• {key.replace('_', ' ').title()}: {len(value)} items")
            # Show first few items if they're simple
            for item in value[:3]:
                if isinstance(item, (str, int, float)):
                    insights.append(f"  - {item}")
                elif isinstance(item, dict) and 'name' in item:
                    insights.append(f"  - {item['name']}")
    
    return "\n".join(insights)

def format_inventory_insights(data: Dict[str, Any]) -> str:
    """Format inventory status data into readable insights"""
    if not data.get('success'):
        return "⚠️ Inventory Status: Unable to retrieve current inventory data"
    
    summary = data.get('summary', {})
    items = data.get('inventory_items', [])
    
    insights = ["📦 **INVENTORY STATUS**"]
    
    # Summary stats
    if summary:
        insights.append(f"• Total in stock: {summary.get('total_in_stock', 0)}")
        insights.append(f"• Low stock items: {summary.get('total_low_stock', 0)}")
        insights.append(f"• Out of stock: {summary.get('total_out_of_stock', 0)}")
        insights.append(f"• Expiring soon: {summary.get('total_expiring_soon', 0)}")
    
    # Critical items
    if items:
        insights.append("\n**ITEMS NEEDING ATTENTION:**")
        for item in items[:5]:  # Show top 5 items
            name = item.get('name', 'Unknown')
            qty = item.get('available_qty', '0')
            unit = item.get('unit', '')
            status = item.get('stock_status', '')
            
            status_emoji = {
                'low_stock': '⚠️',
                'out_of_stock': '🚨',
                'expiring_soon': '⏰',
                'dead_stock': '💀'
            }.get(status, '📦')
            
            insights.append(f"{status_emoji} {name}: {qty} {unit} ({status.replace('_', ' ').title()})")
    
    return "\n".join(insights)

def format_stock_alerts(data: Dict[str, Any]) -> str:
    """Format stock alerts into readable format"""
    if not data.get('success'):
        return "⚠️ Stock Alerts: Unable to retrieve alert data"
    
    alerts = data.get('alerts', [])
    if not alerts:
        return "✅ **STOCK ALERTS**: No critical alerts at this time"
    
    insights = [f"🚨 **STOCK ALERTS** ({len(alerts)} items need attention)"]
    
    # Group by severity
    critical = [a for a in alerts if a.get('severity') == 'Critical']
    high = [a for a in alerts if a.get('severity') == 'High']
    medium = [a for a in alerts if a.get('severity') == 'Medium']
    
    for severity, items in [('CRITICAL', critical), ('HIGH PRIORITY', high), ('MEDIUM', medium)]:
        if items:
            insights.append(f"\n**{severity}:**")
            for alert in items[:3]:  # Top 3 per category
                name = alert.get('product_name', 'Unknown')
                alert_type = alert.get('alert_type', '').replace('_', ' ').title()
                qty = alert.get('current_qty', '0')
                unit = alert.get('unit', '')
                insights.append(f"• {name}: {qty} {unit} ({alert_type})")
    
    return "\n".join(insights)

def format_sales_insights(data: Dict[str, Any]) -> str:
    """Format sales analysis data"""
    if data.get('error'):
        return f"📉 **SALES ANALYSIS**: {data.get('error', 'Unable to retrieve sales data')}"
    
    insights = ["📈 **SALES ANALYSIS**"]
    
    # Extract key sales metrics
    if 'total_sales' in data:
        insights.append(f"• Total Sales: ${data.get('total_sales', 0):,.2f}")
    if 'revenue' in data:
        insights.append(f"• Revenue: ${data.get('revenue', 0):,.2f}")
    if 'growth_rate' in data:
        growth = data.get('growth_rate', 0)
        emoji = "📈" if growth > 0 else "📉" if growth < 0 else "➡️"
        insights.append(f"• Growth Rate: {growth:+.1f}% {emoji}")
    
    # Top performing products
    if 'top_products' in data and isinstance(data['top_products'], list):
        insights.append(f"\n**TOP PERFORMING PRODUCTS:**")
        for i, product in enumerate(data['top_products'][:3], 1):
            if isinstance(product, dict):
                name = product.get('name', 'Unknown')
                sales = product.get('sales', 0)
                insights.append(f"{i}. {name}: ${sales:,.2f}")
    
    return "\n".join(insights)

def format_forecast_insights(data: Dict[str, Any]) -> str:
    """Format forecast data"""
    if data.get('error'):
        return f"🔮 **SALES FORECAST**: {data.get('error', 'Unable to generate forecast data')}"
    
    insights = ["🔮 **SALES FORECAST**"]
    
    if 'forecast_period' in data:
        insights.append(f"• Period: {data['forecast_period']}")
    if 'predicted_sales' in data:
        insights.append(f"• Predicted Sales: ${data.get('predicted_sales', 0):,.2f}")
    if 'confidence_level' in data:
        insights.append(f"• Confidence: {data.get('confidence_level', 0):.1f}%")
    if 'trend' in data:
        trend = data['trend']
        emoji = "📈" if 'up' in trend.lower() else "📉" if 'down' in trend.lower() else "➡️"
        insights.append(f"• Trend: {trend} {emoji}")
    
    return "\n".join(insights)

def format_comparison_insights(data: Dict[str, Any]) -> str:
    """Format period comparison data"""
    if data.get('error'):
        return f"📊 **PERIOD COMPARISON**: {data.get('error', 'Unable to compare periods')}"
    
    insights = ["📊 **PERIOD COMPARISON**"]
    
    if 'current_period' in data and 'previous_period' in data:
        current = data.get('current_period', {})
        previous = data.get('previous_period', {})
        
        if 'sales' in current and 'sales' in previous:
            curr_sales = current['sales']
            prev_sales = previous['sales']
            change = ((curr_sales - prev_sales) / prev_sales * 100) if prev_sales > 0 else 0
            emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            insights.append(f"• Sales Change: {change:+.1f}% {emoji}")
            insights.append(f"• Current: ${curr_sales:,.2f} | Previous: ${prev_sales:,.2f}")
    
    return "\n".join(insights)

def format_performance_insights(data: Dict[str, Any]) -> str:
    """Format product performance data"""
    if data.get('error'):
        return f"🎯 **PRODUCT PERFORMANCE**: {data.get('error', 'Unable to analyze performance')}"
    
    insights = ["🎯 **PRODUCT PERFORMANCE**"]
    
    if 'product_name' in data:
        insights.append(f"• Product: {data['product_name']}")
    if 'performance_score' in data:
        score = data['performance_score']
        emoji = "🟢" if score > 75 else "🟡" if score > 50 else "🔴"
        insights.append(f"• Performance Score: {score}/100 {emoji}")
    if 'sales_velocity' in data:
        insights.append(f"• Sales Velocity: {data['sales_velocity']}")
    
    return "\n".join(insights)

def format_chart_insights(data: Dict[str, Any]) -> str:
    """Format chart generation data"""
    if data.get('error'):
        return f"📊 **CHART DATA**: {data.get('error', 'Unable to generate chart data')}"
    
    insights = ["📊 **CHART DATA GENERATED**"]
    
    if 'chart_type' in data:
        insights.append(f"• Chart Type: {data['chart_type']}")
    if 'data_points' in data:
        insights.append(f"• Data Points: {len(data['data_points'])} points")
    if 'date_range' in data:
        insights.append(f"• Date Range: {data['date_range']}")
    
    return "\n".join(insights)

def format_dashboard_insights(data: Dict[str, Any]) -> str:
    """Format dashboard summary data"""
    if data.get('error'):
        return f"📋 **DASHBOARD SUMMARY**: {data.get('error', 'Unable to generate summary')}"
    
    insights = ["📋 **DASHBOARD SUMMARY**"]
    
    if 'total_revenue' in data:
        insights.append(f"• Total Revenue: ${data['total_revenue']:,.2f}")
    if 'active_products' in data:
        insights.append(f"• Active Products: {data['active_products']}")
    if 'alerts_count' in data:
        insights.append(f"• Active Alerts: {data['alerts_count']}")
    
    return "\n".join(insights)

def format_system_insights(data: Dict[str, Any]) -> str:
    """Format system/backend status data"""
    if data.get('error'):
        return f"🔧 **SYSTEM STATUS**: {data.get('error', 'Unable to check system status')}"
    
    insights = ["🔧 **SYSTEM STATUS**"]
    
    if 'status' in data:
        status = data['status']
        emoji = "🟢" if status == 'healthy' else "🟡" if status == 'warning' else "🔴"
        insights.append(f"• Status: {status.title()} {emoji}")
    if 'uptime' in data:
        insights.append(f"• Uptime: {data['uptime']}")
    if 'response_time' in data:
        insights.append(f"• Response Time: {data['response_time']}ms")
    
    return "\n".join(insights)

def format_endpoints_insights(data: Dict[str, Any]) -> str:
    """Format available endpoints data"""
    if data.get('error'):
        return f"🌐 **API ENDPOINTS**: {data.get('error', 'Unable to retrieve endpoints')}"
    
    insights = ["🌐 **AVAILABLE ENDPOINTS**"]
    
    if 'endpoints' in data and isinstance(data['endpoints'], list):
        insights.append(f"• Total Endpoints: {len(data['endpoints'])}")
        for endpoint in data['endpoints'][:5]:  # Show first 5
            if isinstance(endpoint, dict):
                method = endpoint.get('method', 'GET')
                path = endpoint.get('path', 'unknown')
                insights.append(f"• {method} {path}")
    
    return "\n".join(insights)

def format_growth_insights(data: Dict[str, Any]) -> str:
    """Format growth driver analysis data"""
    if data.get('error'):
        return f"🚀 **GROWTH ANALYSIS**: {data.get('error', 'Unable to analyze growth drivers')}"
    
    insights = ["🚀 **GROWTH DRIVERS**"]
    
    if 'top_drivers' in data and isinstance(data['top_drivers'], list):
        insights.append("**TOP GROWTH FACTORS:**")
        for i, driver in enumerate(data['top_drivers'][:3], 1):
            if isinstance(driver, dict):
                name = driver.get('name', 'Unknown')
                impact = driver.get('impact', 0)
                insights.append(f"{i}. {name}: {impact:+.1f}% impact")
    
    return "\n".join(insights)

def format_seasonal_insights(data: Dict[str, Any]) -> str:
    """Format seasonal trends data"""
    if data.get('error'):
        return f"🌊 **SEASONAL TRENDS**: {data.get('error', 'Unable to analyze seasonal trends')}"
    
    insights = ["🌊 **SEASONAL TRENDS**"]
    
    if 'peak_season' in data:
        insights.append(f"• Peak Season: {data['peak_season']}")
    if 'seasonal_factor' in data:
        factor = data['seasonal_factor']
        emoji = "📈" if factor > 1 else "📉"
        insights.append(f"• Seasonal Factor: {factor:.2f}x {emoji}")
    
    return "\n".join(insights)

def format_velocity_insights(data: Dict[str, Any]) -> str:
    """Format sales velocity data"""
    if data.get('error'):
        return f"⚡ **SALES VELOCITY**: {data.get('error', 'Unable to calculate velocity')}"
    
    insights = ["⚡ **SALES VELOCITY**"]
    
    if 'velocity_score' in data:
        score = data['velocity_score']
        emoji = "🔥" if score > 80 else "⚡" if score > 50 else "🐌"
        insights.append(f"• Velocity Score: {score}/100 {emoji}")
    if 'units_per_day' in data:
        insights.append(f"• Units per Day: {data['units_per_day']}")
    if 'trend' in data:
        insights.append(f"• Trend: {data['trend']}")
    
    return "\n".join(insights)

def format_cookbook_insights(data: Dict[str, Any]) -> str:
    """Format cookbook and recipe data"""
    if data.get('error'):
        return f"📖 **COOKBOOK ANALYSIS**: {data.get('error', 'Unable to retrieve cookbook data')}"
    
    insights = ["📖 **COOKBOOK OVERVIEW**"]
    
    summary = data.get('summary', {})
    if summary:
        insights.append(f"• Total Items: {summary.get('total_items', 0)}")
        insights.append(f"• Menu Items: {summary.get('menu_items', 0)}")
        insights.append(f"• Sub Products: {summary.get('sub_products', 0)}")
        insights.append(f"• Average Price: ${summary.get('average_item_price', 0):.2f}")
    
    business_insights = data.get('business_insights', {})
    if business_insights.get('most_expensive_items'):
        insights.append(f"\n**TOP PRICED ITEMS:**")
        for item in business_insights['most_expensive_items'][:3]:
            name = item.get('name', 'Unknown')
            price = item.get('price', 0)
            insights.append(f"• {name}: ${price:.2f}")
    
    return "\n".join(insights)

def format_recipe_insights(data: Dict[str, Any]) -> str:
    """Format specific recipe details"""
    if data.get('error'):
        return f"👨‍🍳 **RECIPE DETAILS**: {data.get('error', 'Unable to retrieve recipe data')}"
    
    recipe_details = data.get('recipe_details', {})
    insights = [f"👨‍🍳 **RECIPE: {recipe_details.get('name', 'Unknown').upper()}**"]
    
    insights.append(f"• Type: {recipe_details.get('type', 'unknown').replace('_', ' ').title()}")
    insights.append(f"• Price: ${recipe_details.get('price', 0):.2f}")
    
    if 'recipe' in recipe_details:
        recipe = recipe_details['recipe']
        insights.append(f"• Prep Time: {recipe.get('prep_time', 'N/A')}")
        insights.append(f"• Cook Time: {recipe.get('cook_time', 'N/A')}")
        
        if 'ingredients' in recipe:
            ingredients = recipe['ingredients']
            insights.append(f"• Ingredients: {len(ingredients)} items")
    
    ingredient_analysis = data.get('recipe_details', {}).get('ingredient_analysis', {})
    if ingredient_analysis:
        insights.append(f"• Complexity Score: {ingredient_analysis.get('complexity_score', 0):.1f}")
    
    return "\n".join(insights)

def format_menu_insights(data: Dict[str, Any]) -> str:
    """Format menu profitability analysis"""
    if data.get('error'):
        return f"💰 **MENU PROFITABILITY**: {data.get('error', 'Unable to analyze menu profitability')}"
    
    insights = ["💰 **MENU PROFITABILITY ANALYSIS**"]
    
    pricing_insights = data.get('pricing_insights', {})
    if pricing_insights:
        insights.append(f"• Total Menu Items: {pricing_insights.get('total_menu_items', 0)}")
        insights.append(f"• Average Price: ${pricing_insights.get('average_price', 0):.2f}")
        
        price_dist = pricing_insights.get('price_distribution', {})
        insights.append(f"• Low Price Items: {price_dist.get('low_price_items', 0)}")
        insights.append(f"• Medium Price Items: {price_dist.get('medium_price_items', 0)}")
        insights.append(f"• High Price Items: {price_dist.get('high_price_items', 0)}")
    
    top_items = data.get('top_priced_items', [])
    if top_items:
        insights.append(f"\n**HIGHEST PRICED ITEMS:**")
        for item in top_items[:3]:
            name = item.get('product_name', 'Unknown')
            price = item.get('price', 0)
            insights.append(f"• {name}: ${price:.2f}")
    
    return "\n".join(insights)

def format_wastage_insights(data: Dict[str, Any]) -> str:
    """Format wastage analysis data"""
    if data.get('error'):
        return f"🗑️ **WASTAGE ANALYSIS**: {data.get('error', 'Unable to retrieve wastage data')}"
    
    insights = ["🗑️ **WASTAGE ANALYSIS**"]
    
    # Handle different wastage data structures
    if 'wastage_summary' in data:
        summary = data['wastage_summary'].get('summary_statistics', {})
        insights.append(f"• Total Cost: ${summary.get('total_cost', 0):,.2f}")
        insights.append(f"• Analysis Period: {data['wastage_summary'].get('period_analyzed', {}).get('days_analyzed', 0)} days")
        
        business_insights = data['wastage_summary'].get('business_insights', {})
        insights.append(f"• Daily Average: ${business_insights.get('daily_average_cost', 0):.2f}")
        insights.append(f"• Cost Impact: {business_insights.get('cost_impact', 'Unknown')}")
    
    elif 'overall_summary' in data:
        summary = data['overall_summary']
        insights.append(f"• Total Records: {summary.get('total_records', 0)}")
        insights.append(f"• Total Cost: ${summary.get('total_cost', 0):,.2f}")
        insights.append(f"• Average per Incident: ${summary.get('average_cost_per_incident', 0):.2f}")
    
    elif 'summary_statistics' in data:
        summary = data['summary_statistics']
        insights.append(f"• Total Cost: ${summary.get('total_cost', 0):,.2f}")
    
    return "\n".join(insights)

def format_tenant_insights(data: Dict[str, Any]) -> str:
    """Format tenant information"""
    if data.get('error'):
        return f"🏢 **TENANT INFORMATION**: {data.get('error', 'Unable to retrieve tenant data')}"
    
    insights = ["🏢 **TENANT OVERVIEW**"]
    
    business_insights = data.get('business_insights', {})
    if business_insights:
        insights.append(f"• Total Tenants: {business_insights.get('total_tenants', 0)}")
        insights.append(f"• Active Tenants: {business_insights.get('active_tenants', 0)}")
        insights.append(f"• Total Locations: {business_insights.get('total_locations', 0)}")
        insights.append(f"• Multi-location Tenants: {business_insights.get('multi_location_tenants', 0)}")
    
    tenant_info = data.get('tenant_information', [])
    if tenant_info:
        insights.append(f"\n**TENANT DETAILS:**")
        for tenant in tenant_info[:3]:
            name = tenant.get('name', 'Unknown')
            location_count = tenant.get('location_count', 0)
            insights.append(f"• {name}: {location_count} locations")
    
    return "\n".join(insights)

def format_catalog_insights(data: Dict[str, Any]) -> str:
    """Format product catalog analysis"""
    if data.get('error'):
        return f"📋 **PRODUCT CATALOG**: {data.get('error', 'Unable to analyze product catalog')}"
    
    insights = ["📋 **PRODUCT CATALOG ANALYSIS**"]
    
    catalog_analysis = data.get('catalog_analysis', {})
    if catalog_analysis:
        insights.append(f"• Total Products: {catalog_analysis.get('total_products', 0)}")
        
        product_types = catalog_analysis.get('product_types', {})
        for ptype, count in product_types.items():
            insights.append(f"• {ptype.replace('_', ' ').title()}: {count}")
        
        price_analysis = catalog_analysis.get('price_analysis', {})
        if price_analysis:
            insights.append(f"• Total Catalog Value: ${price_analysis.get('total_catalog_value', 0):,.2f}")
            insights.append(f"• Average Price: ${price_analysis.get('average_price', 0):.2f}")
    
    business_insights = data.get('business_insights', {})
    if business_insights:
        insights.append(f"• Catalog Completeness: {business_insights.get('catalog_completeness', 'Unknown')}")
        insights.append(f"• Product Diversity: {business_insights.get('product_diversity', 0)} categories")
    
    return "\n".join(insights)

def format_location_insights(data: Dict[str, Any]) -> str:
    """Format location overview data"""
    if data.get('error'):
        return f"📍 **LOCATION OVERVIEW**: {data.get('error', 'Unable to retrieve location data')}"
    
    insights = ["📍 **LOCATION OVERVIEW**"]
    
    business_insights = data.get('business_insights', {})
    if business_insights:
        insights.append(f"• Total Locations: {business_insights.get('total_locations', 0)}")
        insights.append(f"• Active Locations: {business_insights.get('active_locations', 0)}")
        insights.append(f"• Geographical Spread: {business_insights.get('geographical_spread', 0)} areas")
    
    location_overview = data.get('location_overview', [])
    if location_overview:
        insights.append(f"\n**LOCATION DETAILS:**")
        for location in location_overview[:3]:
            name = location.get('name', 'Unknown')
            city = location.get('city', 'Unknown')
            status = location.get('status', 'unknown')
            insights.append(f"• {name} ({city}): {status.title()}")
    
    return "\n".join(insights)

def format_batch_insights(data: Dict[str, Any]) -> str:
    """Format batch tracking data"""
    if data.get('error'):
        return f"📦 **BATCH TRACKING**: {data.get('error', 'Unable to retrieve batch data')}"
    
    insights = ["📦 **BATCH TRACKING ANALYSIS**"]
    
    batch_metrics = data.get('batch_metrics', {})
    if batch_metrics:
        insights.append(f"• Batch Utilization: {batch_metrics.get('batch_utilization', 0):.1f}%")
        insights.append(f"• Waste Percentage: {batch_metrics.get('waste_percentage', 0):.1f}%")
        insights.append(f"• Value Consumed: ${batch_metrics.get('total_value_consumed', 0):,.2f}")
        insights.append(f"• Value Wasted: ${batch_metrics.get('total_value_wasted', 0):,.2f}")
    
    transaction_analysis = data.get('transaction_analysis', {})
    if transaction_analysis:
        insights.append(f"• Total Transactions: {transaction_analysis.get('total_transactions', 0)}")
        
        quantity_flow = transaction_analysis.get('quantity_flow', {})
        insights.append(f"• Current Balance: {quantity_flow.get('current_balance', 0)}")
    
    business_insights = data.get('business_insights', {})
    if business_insights:
        insights.append(f"• Batch Efficiency: {business_insights.get('batch_efficiency', 'Unknown')}")
        insights.append(f"• Traceability: {business_insights.get('traceability', 'Unknown')}")
    
    return "\n".join(insights)

def generate_final_response(state: ReActState) -> ReActState:
    """
    Generate final conversational response based on ReAct reasoning chain
    """
    
    user_message = state["user_message"]
    reasoning_history = state.get("reasoning_history", [])
    
    # Format tool results into readable insights
    formatted_results = format_tool_results_for_response(reasoning_history)
    
    # Build context from reasoning chain for debugging (optional)
    reasoning_summary = ""
    if reasoning_history:
        reasoning_summary = f"Analysis performed: {len(reasoning_history)} steps using tools: {', '.join(set(step.get('action', '') for step in reasoning_history))}"
    
    # Create final response prompt with formatted results
    response_prompt = f"""
    Based on the analysis results, provide a conversational, helpful response to the user.
    
    User Question: "{user_message}"
    
    ANALYSIS RESULTS:
    {formatted_results}
    
    {reasoning_summary}
    
    Guidelines:
    1. Be conversational and engaging like ChatGPT
    2. Use the structured insights above to provide clear, actionable information
    3. Lead with key insights and actionable recommendations
    4. Use specific numbers and metrics from the analysis
    5. Add relevant emojis for key insights (📈 📉 💡 ⚠️)
    6. Suggest follow-up questions or actions
    7. Keep under 400 words
    8. If there were errors, explain what went wrong and suggest alternatives
    9. Focus on business value and next steps
    
    Generate a helpful, business-focused response based on the structured data above:
    """
    
    try:
        messages = [
            SystemMessage(content="You are a sales analytics assistant that provides insights based on data analysis."),
            HumanMessage(content=response_prompt)
        ]
        
        response = llm.invoke(messages)
        state["final_response"] = response.content
        
        return state
        
    except Exception as e:
        state["final_response"] = f"I analyzed your request using multiple reasoning steps, but encountered an error generating the final response: {str(e)}. Please try rephrasing your question."
        return state

def update_react_session_context(state: ReActState) -> ReActState:
    """
    Update session context with ReAct reasoning data
    """
    
    try:
        session_updates = {
            "last_react_reasoning": {
                "iterations": state.get("iteration_count", 0),
                "tools_used": [step.get("action") for step in state.get("reasoning_history", []) if step.get("action") != "Final Answer"],
                "reasoning_steps": len(state.get("reasoning_history", [])),
                "completed_at": datetime.now().isoformat()
            }
        }
        
        # Extract context from successful tool results
        for step in state.get("reasoning_history", []):
            if step.get("observation") and not step["observation"].startswith("Error"):
                try:
                    result_data = json.loads(step["observation"])
                    if "product_name" in str(result_data):
                        session_updates["last_analyzed_product"] = {
                            "from_react": True,
                            "reasoning_step": step["iteration"]
                        }
                except:
                    pass  # Skip if observation is not valid JSON
        
        state["session_context"] = session_updates
        return state
        
    except Exception as e:
        state["session_context"] = {"error": str(e)}
        return state

# Build the ReAct Graph
def create_react_analytics_graph():
    """Create and return the ReAct analytics LangGraph"""
    
    workflow = StateGraph(ReActState)
    
    # Add nodes
    workflow.add_node("initialize", initialize_react_state)
    workflow.add_node("reasoning", react_reasoning_step)
    workflow.add_node("action", react_action_step)
    workflow.add_node("final_response", generate_final_response)
    workflow.add_node("update_context", update_react_session_context)
    
    # Add edges
    workflow.add_edge(START, "initialize")
    workflow.add_edge("initialize", "reasoning")
    workflow.add_edge("reasoning", "action")
    
    # Conditional edge: continue reasoning or finalize
    workflow.add_conditional_edges(
        "action",
        should_continue_reasoning,
        {
            "reasoning": "reasoning",
            "final_response": "final_response"
        }
    )
    
    workflow.add_edge("final_response", "update_context")
    workflow.add_edge("update_context", END)
    
    # Compile the graph
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app

# Create the ReAct graph instance
react_analytics_graph = create_react_analytics_graph()

async def process_user_message_react(
    message: str,
    session_id: str,
    conversation_history: List[Dict[str, Any]] = None,
    session_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Process a user message through the ReAct analytics flow
    
    Args:
        message: User's input message
        session_id: Session identifier
        conversation_history: Previous conversation messages
        session_context: Previous session context
        
    Returns:
        Response with generated message and ReAct reasoning trace
    """
    
    # Prepare initial state
    initial_state = {
        "user_message": message,
        "session_id": session_id,
        "conversation_history": conversation_history or [],
        "session_context": session_context or {}
    }
    
    try:
        # Run the ReAct graph
        result = await react_analytics_graph.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": session_id}}
        )
        
        return {
            "success": True,
            "response": result["final_response"],
            "method": "react",
            "reasoning_trace": result.get("reasoning_history", []),
            "iterations": result.get("iteration_count", 0),
            "tools_used": [step.get("action") for step in result.get("reasoning_history", []) if step.get("action") != "Final Answer"],
            "session_context": result.get("session_context", {}),
            "metadata": {
                "reasoning_steps": len(result.get("reasoning_history", [])),
                "max_iterations": result.get("max_iterations", 5),
                "processing_time": "calculated_in_production"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "response": f"I apologize, but I encountered an error during reasoning: {str(e)}. Please try again or ask for help.",
            "error": str(e),
            "method": "react",
            "reasoning_trace": [],
            "iterations": 0,
            "session_context": session_context or {}
        }

# Export for use in server
__all__ = ["react_analytics_graph", "process_user_message_react", "ReActState"]
