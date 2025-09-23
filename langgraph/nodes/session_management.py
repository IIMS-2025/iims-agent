"""
Session Context Node for LangGraph
Manages conversation state and context for analytics continuity
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

def update_session_context(
    session_id: str,
    user_message: str,
    ai_response: str,
    intent: str,
    tool_results: List[Dict[str, Any]],
    existing_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Update session context with current interaction data.
    
    Args:
        session_id: Session identifier
        user_message: User's input message
        ai_response: AI's response
        intent: Classified intent
        tool_results: Results from tool calls
        existing_context: Previous session context
        
    Returns:
        Updated session context with analytics metadata
    """
    
    try:
        # Initialize or get existing context
        context = existing_context or {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "message_count": 0,
            "analytics_context": {}
        }
        
        # Update basic session info
        context["last_updated"] = datetime.now().isoformat()
        context["message_count"] = context.get("message_count", 0) + 1
        context["last_intent"] = intent
        context["last_user_message"] = user_message
        
        # Extract and store analytics context from tool results
        analytics_updates = extract_analytics_context(tool_results, intent)
        
        # Update analytics context
        if "analytics_context" not in context:
            context["analytics_context"] = {}
            
        context["analytics_context"].update(analytics_updates)
        
        # Store conversation pattern for follow-ups
        context["conversation_pattern"] = analyze_conversation_pattern(
            user_message, intent, context.get("conversation_pattern", [])
        )
        
        return {
            "success": True,
            "session_context": context,
            "updates_made": list(analytics_updates.keys()),
            "context_size": len(json.dumps(context))
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "session_context": existing_context or {}
        }

def extract_analytics_context(
    tool_results: List[Dict[str, Any]], 
    intent: str
) -> Dict[str, Any]:
    """Extract relevant analytics context from tool results."""
    
    analytics_context = {}
    
    for tool_result in tool_results:
        result_data = tool_result.get("result", {})
        tool_name = tool_result.get("tool", "")
        
        # Extract product context
        if "product_name" in result_data:
            analytics_context["lastAnalyzedProduct"] = {
                "name": result_data["product_name"],
                "id": result_data.get("product_id"),
                "type": result_data.get("product_type"),
                "last_metrics": {
                    "revenue": result_data.get("total_revenue") or result_data.get("predicted_revenue"),
                    "growth_rate": result_data.get("growth_rate"),
                    "analyzed_at": datetime.now().isoformat()
                }
            }
            
        # Extract time period context
        if "time_period" in result_data:
            analytics_context["lastTimeframe"] = result_data["time_period"]
            
        # Extract analysis type context
        if tool_name in ["analyze_sales_data", "forecast_sales", "analyze_product_performance"]:
            analytics_context["currentAnalysisType"] = tool_name
            analytics_context["lastAnalysisResults"] = {
                "tool": tool_name,
                "success": result_data.get("success", False),
                "summary": result_data.get("insights", [])[:2] if result_data.get("insights") else []
            }
            
        # Extract chart preferences
        if tool_name == "generate_chart_data" and result_data.get("success"):
            analytics_context["chartPreferences"] = {
                "last_chart_type": result_data.get("metadata", {}).get("chart_type"),
                "preferred_data_source": result_data.get("metadata", {}).get("data_source")
            }
            
        # Store pending comparisons for follow-ups
        if intent == "compare_periods":
            analytics_context["pendingComparisons"] = [{
                "type": "period_comparison",
                "current": result_data.get("comparison", {}).get("current_period"),
                "previous": result_data.get("comparison", {}).get("comparison_period"),
                "metric": result_data.get("comparison", {}).get("metric")
            }]
            
    return analytics_context

def analyze_conversation_pattern(
    user_message: str,
    intent: str,
    existing_pattern: List[str] = None
) -> List[str]:
    """Analyze conversation patterns for better follow-up prediction."""
    
    pattern = existing_pattern or []
    
    # Add current intent to pattern
    pattern.append(intent)
    
    # Keep only last 5 intents for pattern analysis
    pattern = pattern[-5:]
    
    return pattern

def resolve_follow_up_context(
    user_message: str,
    session_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Resolve follow-up references using session context.
    
    Args:
        user_message: Current user message
        session_context: Previous session context
        
    Returns:
        Resolved parameters for follow-up queries
    """
    
    message_lower = user_message.lower()
    resolved_params = {}
    
    # Product reference resolution
    product_references = ["that product", "it", "same item", "that item", "for that"]
    if any(ref in message_lower for ref in product_references):
        last_product = session_context.get("analytics_context", {}).get("lastAnalyzedProduct")
        if last_product:
            resolved_params["product_name"] = last_product.get("name")
            resolved_params["product_id"] = last_product.get("id")
            resolved_params["context_source"] = "lastAnalyzedProduct"
            
    # Time period reference resolution
    period_references = ["same period", "that timeframe", "same time"]
    if any(ref in message_lower for ref in period_references):
        last_timeframe = session_context.get("analytics_context", {}).get("lastTimeframe")
        if last_timeframe:
            resolved_params["time_period"] = last_timeframe
            resolved_params["context_source"] = "lastTimeframe"
            
    # Analysis type continuation
    continuation_words = ["continue", "more", "also", "and", "plus"]
    if any(word in message_lower for word in continuation_words):
        last_analysis = session_context.get("analytics_context", {}).get("currentAnalysisType")
        if last_analysis:
            resolved_params["analysis_continuation"] = last_analysis
            
    return resolved_params

def get_clarification_suggestions(
    intent: str,
    partial_slots: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate clarification questions when slots are incomplete.
    
    Args:
        intent: User's classified intent
        partial_slots: Partially filled slots
        
    Returns:
        Clarification questions and suggestions
    """
    
    suggestions = {}
    
    if intent == "analyze_sales_trends":
        if "time_period" not in partial_slots:
            suggestions["time_period"] = {
                "question": "Which time period would you like to analyze?",
                "options": ["Last week", "Last month", "This month", "Last quarter"]
            }
        if "product_name" not in partial_slots and "category" not in partial_slots:
            suggestions["scope"] = {
                "question": "Would you like to analyze all products or focus on specific items?",
                "options": ["All products", "Menu items only", "Specific product", "Raw materials"]
            }
            
    elif intent == "forecast_sales":
        if "forecast_days" not in partial_slots:
            suggestions["forecast_period"] = {
                "question": "How far ahead would you like me to forecast?",
                "options": ["7 days", "30 days", "90 days"]
            }
        if "product_name" not in partial_slots:
            suggestions["product_scope"] = {
                "question": "Which products should I forecast?",
                "options": ["All menu items", "Kerala Burger", "Chicken Burger", "Specific product"]
            }
            
# elif intent == "update_stock_single":  # Removed - analytics should be read-only
        missing_params = []
        if "product_name" not in partial_slots:
            missing_params.append("product name")
        if "qty" not in partial_slots:
            missing_params.append("quantity")
        if "unit" not in partial_slots:
            missing_params.append("unit")
            
        if missing_params:
            suggestions["missing_params"] = {
                "question": f"I need the following information: {', '.join(missing_params)}",
                "example": "Example: 'Add 20 kg to tomatoes' or 'Update Kerala Burger stock by 15 pcs'"
            }
            
    return {
        "intent": intent,
        "partial_slots": partial_slots,
        "clarification_needed": len(suggestions) > 0,
        "suggestions": suggestions,
        "completion_percentage": len(partial_slots) / max(1, len(suggestions) + len(partial_slots))
    }

# Export functions
__all__ = [
    "extract_parameters_from_message",
    "update_session_context", 
    "resolve_follow_up_context",
    "get_clarification_suggestions"
]
