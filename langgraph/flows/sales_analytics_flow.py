"""
Main Sales Analytics Flow for LangGraph
Orchestrates conversation flow with tool calling for sales analysis
"""

import os
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph import START
from langgraph.checkpoint.memory import MemorySaver
import json

# Import tools
from ..tools.sales_analytics_tool import get_total_sales
from ..tools.forecasting_tool import forecast_sales, forecast_inventory_needs
from ..tools.inventory_tool import get_inventory_status, check_stock_alerts, get_inventory_analytics
from ..tools.comparison_tool import compare_inventory_performance, compare_menu_items
from ..tools.chart_data_tool import generate_inventory_chart_data, generate_sales_chart_data
from ..tools.report_generation_tool import generate_comprehensive_business_report
from ..tools.backend_health_tool import check_backend_status, get_available_endpoints

# Define the state for our graph
class AnalyticsState(dict):
    """State for the sales analytics conversation flow"""
    user_message: str
    session_id: str
    conversation_history: List[Dict[str, Any]]
    extracted_intent: Optional[str]
    extracted_slots: Dict[str, Any]
    tool_results: List[Dict[str, Any]]
    final_response: str
    session_context: Dict[str, Any]

# Initialize LLM
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)

def extract_intent_and_slots(state: AnalyticsState) -> AnalyticsState:
    """
    Extract user intent and parameters from the message using LLM
    """
    
    user_message = state["user_message"]
    conversation_history = state.get("conversation_history", [])
    
    # Create prompt for intent extraction
    intent_prompt = f"""
    Analyze this user message and extract the intent and parameters for a sales analytics assistant.
    
    User message: "{user_message}"
    
    Previous conversation context: {json.dumps(conversation_history[-3:] if conversation_history else [])}
    
    Classify the intent as one of:
    - analyze_sales_trends: Questions about sales patterns, trends, performance over time
    - forecast_sales: Requests for sales predictions, demand forecasting
    - view_inventory_status: Questions about current stock levels, inventory health
    - analyze_product_performance: Comparisons of product performance, rankings
    - compare_periods: Comparing metrics between different time periods
    - view_specific_metrics: Specific revenue, profit, or performance questions
    - generate_report: Requests for reports or summaries
    - create_chart: Requests for charts, graphs, or visual data
    - help: General help or capability questions
    - clarify: Unclear or ambiguous requests
    - fallback: Unrecognized intent
    
    Extract these parameters if present:
    - time_period: (last_week, last_month, this_month, last_quarter, etc.)
    - product_name: Name of specific product
    - category: Product category (menu, raw_material, etc.)
    - metric_type: (revenue, quantity_sold, profit_margin, etc.)
    - forecast_days: Number of days for forecasting
    - chart_type: (line, bar, pie, trend)
    - comparison_period: Period to compare against
    
    Return JSON format:
    {{
        "intent": "extracted_intent",
        "confidence": 0.95,
        "slots": {{
            "parameter_name": "extracted_value"
        }}
    }}
    """
    
    try:
        response = llm.invoke([HumanMessage(content=intent_prompt)])
        
        # Parse the LLM response
        result_text = response.content
        
        # Try to extract JSON from the response
        import re
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            intent_data = json.loads(json_match.group())
        else:
            # Fallback parsing
            intent_data = {
                "intent": "fallback",
                "confidence": 0.5,
                "slots": {}
            }
            
        state["extracted_intent"] = intent_data["intent"]
        state["extracted_slots"] = intent_data["slots"]
        
        return state
        
    except Exception as e:
        state["extracted_intent"] = "fallback"
        state["extracted_slots"] = {"error": str(e)}
        return state

async def route_to_tools(state: AnalyticsState) -> AnalyticsState:
    """
    Route to appropriate tools based on extracted intent
    """
    
    intent = state["extracted_intent"]
    slots = state["extracted_slots"]
    tool_results = []
    
    try:
        if intent == "analyze_sales_trends":
            # Call sales analytics tool
            result = await get_total_sales.ainvoke({
                "date_range": slots.get("time_period", "last_30_days"),
                "include_forecasting": True
            })
            tool_results.append({"tool": "get_total_sales", "result": result})
            
        elif intent == "forecast_sales":
            # Call forecasting tool
            result = await forecast_sales.ainvoke({
                "product_id": slots.get("product_id"),
                "product_name": slots.get("product_name"),
                "category": slots.get("category"),
                "forecast_days": slots.get("forecast_days", 30)
            })
            tool_results.append({"tool": "forecast_sales", "result": result})
            
        elif intent == "view_inventory_status":
            # Call inventory tool
            result = await get_inventory_status.ainvoke({
                "filter_status": slots.get("filter_status"),
                "product_id": slots.get("product_id"),
                "include_sales_context": True
            })
            tool_results.append({"tool": "get_inventory_status", "result": result})
            
        elif intent == "analyze_product_performance":
            # Get product performance analysis
            result = await get_total_sales.ainvoke({
                "date_range": slots.get("time_period", "last_30_days"),
                "include_forecasting": True
            })
            tool_results.append({"tool": "get_total_sales", "result": result})
                
        elif intent == "compare_periods":
            # Call comparison tool
            result = await compare_inventory_performance.ainvoke({
                "current_period": slots.get("current_period", "current_month"),
                "comparison_period": slots.get("comparison_period", "previous_month"),
                "metric": slots.get("metric", "revenue"),
                "category": slots.get("category")
            })
            tool_results.append({"tool": "compare_inventory_performance", "result": result})
            
        elif intent == "create_chart":
            # Call chart data tool
            data_source = slots.get("data_source", "sales")
            if data_source == "inventory":
                result = await generate_inventory_chart_data.ainvoke({
                    "chart_type": slots.get("chart_type", "bar"),
                    "category_filter": slots.get("product_filter"),
                    "time_period": slots.get("time_period", "current")
                })
                tool_results.append({"tool": "generate_inventory_chart_data", "result": result})
            else:
                result = await generate_sales_chart_data.ainvoke({
                    "chart_type": slots.get("chart_type", "line"),
                    "time_period": slots.get("time_period", "last_month"),
                    "product_filter": slots.get("product_filter")
                })
                tool_results.append({"tool": "generate_sales_chart_data", "result": result})
            
        elif intent == "generate_report":
            # Create comprehensive business report
            result = await generate_comprehensive_business_report.ainvoke({
                "report_type": slots.get("report_type", "executive_summary"),
                "include_forecasts": True,
                "include_recommendations": True
            })
            tool_results.append({"tool": "generate_comprehensive_business_report", "result": result})
            
        elif intent == "help":
            # No tools needed, direct response
            tool_results.append({
                "tool": "help_response",
                "result": {
                    "success": True,
                    "help_content": {
                        "capabilities": [
                            "📊 Analyze sales trends and patterns",
                            "🔮 Forecast future sales performance", 
                            "📈 Compare performance across time periods",
                            "🏆 Rank product performance",
                            "📦 Check inventory status with sales context",
                            "📊 Generate charts and visualizations"
                        ],
                        "example_questions": [
                            "Show me sales trends for last month",
                            "Which products are performing best?",
                            "Predict Kerala Burger sales for next 30 days",
                            "Compare this month vs last month revenue",
                            "What inventory needs attention?",
                            "Create a sales dashboard"
                        ]
                    }
                }
            })
            
        else:
            # Fallback - try to get general inventory status
            result = await get_inventory_status.ainvoke({"include_sales_context": True})
            tool_results.append({"tool": "get_inventory_status", "result": result})
            
        state["tool_results"] = tool_results
        return state
        
    except Exception as e:
        state["tool_results"] = [{
            "tool": "error",
            "result": {
                "error": True,
                "message": f"Tool execution failed: {str(e)}"
            }
        }]
        return state

def generate_response(state: AnalyticsState) -> AnalyticsState:
    """
    Generate final conversational response using LLM with tool results
    """
    
    user_message = state["user_message"]
    intent = state["extracted_intent"]
    tool_results = state.get("tool_results", [])
    conversation_history = state.get("conversation_history", [])
    
    # Create system prompt
    system_prompt = """You are a sales analytics and forecasting assistant for Kochi Burger Junction. You help analyze sales trends, predict future performance, and provide data-driven insights. Use the provided tools to query sales data, inventory levels, and generate forecasts. Be conversational like ChatGPT but focus on actionable business insights. Present data clearly with key metrics, trends, and recommendations. If you need specific data, use the available tools. Keep responses engaging but under 400 words. Use emojis sparingly for key insights (📈 📉 💡 ⚠️)."""
    
    # Prepare context for LLM
    context = {
        "user_message": user_message,
        "intent": intent,
        "tool_results": tool_results,
        "conversation_history": conversation_history[-5:]  # Last 5 messages
    }
    
    # Create response prompt
    response_prompt = f"""
    Based on the user's question and the tool results, provide a conversational, helpful response.
    
    User asked: "{user_message}"
    Detected intent: {intent}
    
    Tool results: {json.dumps(tool_results, indent=2)}
    
    Guidelines:
    1. Be conversational and engaging like ChatGPT
    2. Lead with key insights and actionable recommendations
    3. Use specific numbers and metrics from the tool results
    4. Add relevant emojis for key insights (📈 📉 💡 ⚠️)
    5. Suggest follow-up questions or actions
    6. Keep under 400 words
    7. If there are errors in tool results, explain them clearly and suggest alternatives
    
    Generate a helpful, business-focused response:
    """
    
    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=response_prompt)
        ]
        
        response = llm.invoke(messages)
        state["final_response"] = response.content
        
        return state
        
    except Exception as e:
        state["final_response"] = f"I apologize, but I encountered an error while analyzing your request: {str(e)}. Please try rephrasing your question or ask for help to see what I can do."
        return state

def update_session_context(state: AnalyticsState) -> AnalyticsState:
    """
    Update session context with conversation data for follow-ups
    """
    
    try:
        # Extract relevant context from tool results
        session_updates = {}
        
        for tool_result in state.get("tool_results", []):
            result_data = tool_result.get("result", {})
            
            # Track analyzed products
            if "product_name" in result_data:
                session_updates["last_analyzed_product"] = {
                    "name": result_data["product_name"],
                    "id": result_data.get("product_id"),
                    "metrics": result_data
                }
                
            # Track time periods
            if "time_period" in result_data:
                session_updates["last_timeframe"] = result_data["time_period"]
                
            # Track analysis type
            if tool_result.get("tool") in ["analyze_sales_data", "forecast_sales"]:
                session_updates["current_analysis_type"] = tool_result["tool"]
                
        state["session_context"] = session_updates
        return state
        
    except Exception as e:
        state["session_context"] = {"error": str(e)}
        return state

# Build the graph
def create_sales_analytics_graph():
    """Create and return the sales analytics LangGraph"""
    
    workflow = StateGraph(AnalyticsState)
    
    # Add nodes
    workflow.add_node("extract_intent", extract_intent_and_slots)
    workflow.add_node("call_tools", route_to_tools)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("update_context", update_session_context)
    
    # Add edges
    workflow.add_edge(START, "extract_intent")
    workflow.add_edge("extract_intent", "call_tools")
    workflow.add_edge("call_tools", "generate_response")
    workflow.add_edge("generate_response", "update_context")
    workflow.add_edge("update_context", END)
    
    # Compile the graph
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app

# Create the graph instance
sales_analytics_graph = create_sales_analytics_graph()

async def process_user_message(
    message: str,
    session_id: str,
    conversation_history: List[Dict[str, Any]] = None,
    session_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Process a user message through the sales analytics flow
    
    Args:
        message: User's input message
        session_id: Session identifier
        conversation_history: Previous conversation messages
        session_context: Previous session context
        
    Returns:
        Response with generated message and updated context
    """
    
    # Prepare initial state
    initial_state = {
        "user_message": message,
        "session_id": session_id,
        "conversation_history": conversation_history or [],
        "session_context": session_context or {}
    }
    
    try:
        # Run the graph
        result = await sales_analytics_graph.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": session_id}}
        )
        
        return {
            "success": True,
            "response": result["final_response"],
            "intent": result.get("extracted_intent"),
            "tool_results": result.get("tool_results", []),
            "session_context": result.get("session_context", {}),
            "metadata": {
                "tools_used": [tr.get("tool") for tr in result.get("tool_results", [])],
                "processing_time": "calculated_in_production"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "response": f"I apologize, but I encountered an error processing your request: {str(e)}. Please try again or ask for help.",
            "error": str(e),
            "intent": "error",
            "tool_results": [],
            "session_context": session_context or {}
        }

# Export for use in server
__all__ = ["sales_analytics_graph", "process_user_message", "AnalyticsState"]
