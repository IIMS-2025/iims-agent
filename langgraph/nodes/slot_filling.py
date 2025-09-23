"""
Parameter Extraction/Slot-filling Node for LangGraph
Extracts required parameters for database tools and analytics queries
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import os
import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Initialize LLM
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    temperature=0.2,  # Low temperature for consistent parameter extraction
    api_key=os.getenv("OPENAI_API_KEY")
)

def extract_parameters_from_message(
    user_message: str,
    intent: str,
    conversation_history: list = None,
    session_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Extract structured parameters (slots) from user message based on intent.
    
    Args:
        user_message: The user's input message
        intent: Previously classified intent
        conversation_history: Previous conversation for context
        session_context: Session data for follow-up resolution
        
    Returns:
        Structured slots object with extracted parameters
    """
    
    # Initialize slots
    slots = {}
    
    try:
        # Use OpenAI for sophisticated parameter extraction if available
        if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "your-openai-api-key-here":
            slots = extract_slots_with_llm(user_message, intent, conversation_history, session_context)
        else:
            # Fallback to rule-based extraction
            slots = extract_slots_fallback(user_message, intent, session_context)
            
        # Post-process and validate slots
        slots = validate_and_normalize_slots(slots, intent)
        
        return {
            "success": True,
            "intent": intent,
            "extracted_slots": slots,
            "context_used": bool(session_context and any(key in user_message.lower() for key in ["that", "it", "same", "previous"])),
            "completeness": calculate_slot_completeness(slots, intent)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "extracted_slots": {},
            "intent": intent
        }

def extract_slots_with_llm(
    user_message: str,
    intent: str,
    conversation_history: list = None,
    session_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Extract parameters using OpenAI LLM for sophisticated understanding."""
    
    context_info = ""
    if conversation_history:
        context_info += f"\n\nConversation history: {json.dumps(conversation_history[-2:])}"
    if session_context:
        context_info += f"\n\nSession context: {json.dumps(session_context)}"
    
    slot_prompt = f"""
    Extract parameters from this user message for intent: {intent}
    
    User message: "{user_message}"
    {context_info}
    
    PARAMETER DEFINITIONS BY INTENT:
    
    For analyze_sales_trends:
    - time_period: last_week, last_month, this_month, last_quarter, custom
    - start_date: ISO date string for custom periods
    - end_date: ISO date string for custom periods  
    - product_name: Specific product mentioned
    - product_category: menu, raw_material, sub_product
    - metric_type: revenue, quantity_sold, profit_margin, turnover_rate
    - group_by: day, week, month, product, category
    
    For forecast_sales:
    - product_name: Product to forecast
    - product_category: Category to forecast
    - forecast_days: 7, 30, 90 (number of days)
    - include_confidence: true/false
    
    For view_inventory_status:
    - filter_status: low_stock, out_of_stock, expiring_soon, dead_stock
    - product_name: Specific product
    - include_batches: true/false
    
    For analyze_product_performance:
    - time_period: Analysis period
    - metric: revenue, quantity_sold, profit_margin
    - top_n: Number of top performers (default 10)
    - category: Product category filter
    
    For compare_periods:
    - current_period: this_week, this_month, this_quarter
    - comparison_period: last_week, last_month, last_quarter
    - metric: revenue, sales_volume, profit_margin
    - product_name: Specific product to compare
    
    For create_chart:
    - chart_type: line, bar, pie, trend
    - data_source: sales, inventory, forecasts, performance
    - time_period: Period for chart data
    - product_filter: Product/category filter
    
# For update_stock_single:  # Removed - analytics should be read-only
    - product_name: Product to update
    - qty: Quantity (extract numbers)
    - unit: kg, pcs, ml, etc.
    - tx_type: purchase, usage, adjustment
    - reason: Reason for update
    
    CONTEXT RESOLUTION:
    - If user says "that product", "it", "same item" - use session context for product_name
    - If user says "same period", "that timeframe" - use session context for time_period
    - For follow-ups like "forecast for that", inherit product from previous analysis
    
    Return ONLY valid JSON:
    {{
        "time_period": "extracted_value_or_null",
        "product_name": "extracted_value_or_null", 
        "metric": "extracted_value_or_null",
        "forecast_days": "extracted_number_or_null",
        "chart_type": "extracted_value_or_null",
        "qty": "extracted_number_or_null",
        "unit": "extracted_value_or_null",
        "other_params": {{}}
    }}
    """
    
    try:
        response = llm.invoke([HumanMessage(content=slot_prompt)])
        result_text = response.content
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return {}
            
    except Exception as e:
        # Fallback to rule-based if LLM fails
        return extract_slots_fallback(user_message, intent, session_context)

def extract_slots_fallback(
    user_message: str,
    intent: str,
    session_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Rule-based parameter extraction fallback."""
    
    message_lower = user_message.lower()
    slots = {}
    
    # Time period extraction
    time_patterns = {
        "last_week": ["last week", "previous week"],
        "this_week": ["this week", "current week"],
        "last_month": ["last month", "previous month"],
        "this_month": ["this month", "current month"],
        "last_quarter": ["last quarter", "previous quarter"],
        "this_quarter": ["this quarter", "current quarter"]
    }
    
    for period, patterns in time_patterns.items():
        if any(pattern in message_lower for pattern in patterns):
            slots["time_period"] = period
            break
            
    # Product name extraction
    product_keywords = ["kerala burger", "chicken burger", "fish burger", "tomatoes", "ground beef", "burger buns"]
    for product in product_keywords:
        if product in message_lower:
            slots["product_name"] = product.title()
            break
            
    # Metric extraction
    if any(word in message_lower for word in ["revenue", "money", "₹", "sales"]):
        slots["metric_type"] = "revenue"
    elif any(word in message_lower for word in ["quantity", "units", "sold", "volume"]):
        slots["metric_type"] = "quantity_sold"
    elif any(word in message_lower for word in ["margin", "profit"]):
        slots["metric_type"] = "profit_margin"
        
    # Number extraction for forecasting and quantities
    numbers = re.findall(r'\d+', user_message)
    if numbers:
        first_number = int(numbers[0])
        
        if intent == "forecast_sales" and any(word in message_lower for word in ["day", "week", "month"]):
            if first_number in [7, 30, 90]:
                slots["forecast_days"] = first_number
# elif intent == "update_stock_single":  # Removed - analytics should be read-only
# slots["qty"] = float(first_number)  # Removed - analytics should be read-only
            
    # Unit extraction for stock updates - REMOVED (analytics should be read-only)
                
    # Chart type extraction
    if intent == "create_chart":
        chart_types = {"line": ["line", "trend"], "bar": ["bar", "column"], "pie": ["pie", "donut"]}
        for chart_type, keywords in chart_types.items():
            if any(keyword in message_lower for keyword in keywords):
                slots["chart_type"] = chart_type
                break
                
    # Context resolution for follow-ups
    if session_context:
        # Resolve "that product", "it", etc.
        if any(word in message_lower for word in ["that", "it", "same"]) and "product" in message_lower:
            if session_context.get("lastAnalyzedProduct"):
                slots["product_name"] = session_context["lastAnalyzedProduct"].get("name")
                slots["product_id"] = session_context["lastAnalyzedProduct"].get("id")
                
        # Resolve timeframe references
        if any(word in message_lower for word in ["same period", "that timeframe"]):
            if session_context.get("lastTimeframe"):
                slots["time_period"] = session_context["lastTimeframe"]
                
    return slots

def validate_and_normalize_slots(slots: Dict[str, Any], intent: str) -> Dict[str, Any]:
    """Validate and normalize extracted slots."""
    
    # Normalize time periods
    if "time_period" in slots:
        period = slots["time_period"].lower().replace(" ", "_")
        valid_periods = ["last_week", "this_week", "last_month", "this_month", "last_quarter", "this_quarter"]
        if period in valid_periods:
            slots["time_period"] = period
        else:
            del slots["time_period"]  # Remove invalid periods
            
    # Normalize product names
    if "product_name" in slots:
        # Title case for consistency
        slots["product_name"] = slots["product_name"].title()
        
    # Validate forecast days
    if "forecast_days" in slots:
        if slots["forecast_days"] not in [7, 30, 90]:
            # Map to closest valid value
            if slots["forecast_days"] <= 10:
                slots["forecast_days"] = 7
            elif slots["forecast_days"] <= 45:
                slots["forecast_days"] = 30
            else:
                slots["forecast_days"] = 90
                
    # Clean up null/empty values
    slots = {k: v for k, v in slots.items() if v is not None and v != ""}
    
    return slots

def calculate_slot_completeness(slots: Dict[str, Any], intent: str) -> float:
    """Calculate how complete the extracted slots are for the given intent."""
    
    required_slots = {
        "analyze_sales_trends": ["time_period"],
        "forecast_sales": ["forecast_days"],
        "view_inventory_status": [],  # No required slots
        "analyze_product_performance": ["metric"],
        "compare_periods": ["current_period", "comparison_period"],
        "create_chart": ["chart_type", "data_source"],
# "update_stock_single": ["product_name", "qty", "unit"],  # Removed - analytics should be read-only
        "generate_report": [],
        "view_specific_metrics": ["product_name", "metric_type"],
        "help": [],
        "clarify": [],
        "fallback": []
    }
    
    intent_requirements = required_slots.get(intent, [])
    if not intent_requirements:
        return 1.0  # No requirements means 100% complete
        
    filled_requirements = sum(1 for req in intent_requirements if req in slots)
    return filled_requirements / len(intent_requirements)

# Export functions for use in flows
__all__ = [
    "extract_intent_from_message",
    "extract_parameters_from_message", 
    "classify_intent_fallback",
    "validate_and_normalize_slots"
]
