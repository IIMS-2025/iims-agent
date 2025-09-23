"""
Fallback & Clarify Node for LangGraph
Handles missing parameters and provides suggestions for unclear requests
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import random

def handle_fallback_intent(
    user_message: str,
    session_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Handle unrecognized or out-of-scope requests with helpful suggestions.
    
    Args:
        user_message: User's input message
        session_context: Current session context
        
    Returns:
        Helpful fallback response with capability suggestions
    """
    
    try:
        # Analyze what the user might be trying to do
        message_lower = user_message.lower()
        
        # Suggest related capabilities
        suggestions = []
        
        if any(word in message_lower for word in ["customer", "review", "rating"]):
            suggestions.extend([
                "I can analyze product performance and sales trends",
                "Try asking: 'Which products are performing best?'"
            ])
        elif any(word in message_lower for word in ["cost", "expense", "budget"]):
            suggestions.extend([
                "I can analyze profit margins and revenue trends",
                "Try asking: 'Show me profit margins by product'"
            ])
        elif any(word in message_lower for word in ["competitor", "market", "industry"]):
            suggestions.extend([
                "I focus on your internal sales and inventory data",
                "Try asking: 'Compare this month vs last month performance'"
            ])
        elif any(word in message_lower for word in ["staff", "employee", "schedule"]):
            suggestions.extend([
                "I can provide sales insights that help with staffing decisions",
                "Try asking: 'When are our peak sales hours?'"
            ])
        else:
            suggestions.extend([
                "I can help with sales analysis, forecasting, and inventory insights",
                "Try asking about trends, forecasts, or product performance"
            ])
            
        # Get recent successful examples from session
        recent_examples = get_recent_successful_examples(session_context)
        
        return {
            "success": True,
            "response_type": "fallback",
            "user_message": user_message,
            "suggestions": suggestions,
            "recent_examples": recent_examples,
            "capabilities": [
                "📊 Sales trend analysis",
                "🔮 Sales forecasting", 
                "🏆 Product performance rankings",
                "📈 Period comparisons",
                "📦 Inventory insights",
                "📊 Chart generation"
            ],
            "sample_questions": [
                "Show me sales trends for last month",
                "Which products are performing best?",
                "Predict Kerala Burger sales for next 30 days",
                "Compare this month vs last month revenue",
                "What inventory needs attention?"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response_type": "fallback",
            "fallback_message": "I'm here to help with sales analytics. Try asking about sales trends, forecasts, or product performance."
        }

def handle_clarification_request(
    user_message: str,
    intent: str,
    partial_slots: Dict[str, Any],
    session_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Handle requests that need clarification due to missing or ambiguous parameters.
    
    Args:
        user_message: User's input message
        intent: Classified intent
        partial_slots: Partially extracted parameters
        session_context: Current session context
        
    Returns:
        Clarification questions with quick-reply suggestions
    """
    
    try:
        clarifications = generate_clarification_questions(intent, partial_slots, session_context)
        
        # Format clarification response
        response_data = {
            "success": True,
            "response_type": "clarification",
            "intent": intent,
            "partial_slots": partial_slots,
            "clarification_questions": clarifications["questions"],
            "quick_replies": clarifications["quick_replies"],
            "context_suggestions": clarifications.get("context_suggestions", []),
            "estimated_completion": clarifications["completion_percentage"]
        }
        
        return response_data
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response_type": "clarification",
            "fallback_message": "Could you provide more details about what you'd like to analyze?"
        }

def generate_clarification_questions(
    intent: str,
    partial_slots: Dict[str, Any],
    session_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Generate specific clarification questions based on intent and missing slots."""
    
    questions = []
    quick_replies = []
    context_suggestions = []
    
    if intent == "analyze_sales_trends":
        if "time_period" not in partial_slots:
            questions.append("Which time period would you like me to analyze?")
            quick_replies.extend(["Last week", "Last month", "This month", "Last quarter"])
            
        if "product_name" not in partial_slots and "category" not in partial_slots:
            questions.append("Should I analyze all products or focus on specific items?")
            quick_replies.extend(["All menu items", "Kerala Burger", "Chicken items", "All products"])
            
        if not questions:
            questions.append("Would you like me to analyze all products for the specified period?")
            
    elif intent == "forecast_sales":
        if "forecast_days" not in partial_slots:
            questions.append("How many days ahead should I forecast?")
            quick_replies.extend(["7 days", "30 days", "90 days"])
            
        if "product_name" not in partial_slots and "category" not in partial_slots:
            questions.append("Which products should I forecast?")
            quick_replies.extend(["All menu items", "Kerala Burger", "Chicken Burger", "Top performers"])
            
    elif intent == "compare_periods":
        if "current_period" not in partial_slots:
            questions.append("What's the current period you want to analyze?")
            quick_replies.extend(["This week", "This month", "This quarter"])
            
        if "comparison_period" not in partial_slots:
            questions.append("What period should I compare it against?")
            quick_replies.extend(["Last week", "Last month", "Last quarter", "Same period last year"])
            
        if "metric" not in partial_slots:
            questions.append("Which metric should I compare?")
            quick_replies.extend(["Revenue", "Sales volume", "Profit margin", "All metrics"])
            
# elif intent == "update_stock_single":  # Removed - analytics should be read-only
        missing = []
        if "product_name" not in partial_slots:
            missing.append("product name")
        if "qty" not in partial_slots:
            missing.append("quantity") 
        if "unit" not in partial_slots:
            missing.append("unit")
            
        if missing:
            questions.append(f"I need the {', '.join(missing)} to update stock.")
            questions.append("Please specify in format: 'Add [quantity] [unit] to [product]'")
            quick_replies.extend(["20 kg tomatoes", "50 pcs burger buns", "15 kg ground beef"])
            
    elif intent == "create_chart":
        if "chart_type" not in partial_slots:
            questions.append("What type of chart would you like?")
            quick_replies.extend(["Line chart", "Bar chart", "Pie chart", "Trend chart"])
            
        if "data_source" not in partial_slots:
            questions.append("What data should I chart?")
            quick_replies.extend(["Sales data", "Inventory levels", "Product performance", "Forecasts"])
            
    # Add context suggestions from session
    if session_context:
        last_product = session_context.get("analytics_context", {}).get("lastAnalyzedProduct")
        if last_product:
            context_suggestions.append(f"Continue with {last_product.get('name')} analysis")
            
        last_timeframe = session_context.get("analytics_context", {}).get("lastTimeframe")
        if last_timeframe:
            context_suggestions.append(f"Use {last_timeframe} timeframe")
            
    # Default suggestions if no specific questions
    if not questions:
        questions.append("Could you provide more specific details about what you'd like to analyze?")
        quick_replies.extend(["Sales trends", "Product performance", "Forecasting", "Inventory status"])
        
    completion_percentage = len(partial_slots) / max(1, len(partial_slots) + len(questions))
    
    return {
        "questions": questions,
        "quick_replies": quick_replies,
        "context_suggestions": context_suggestions,
        "completion_percentage": completion_percentage
    }

def suggest_related_actions(
    intent: str,
    successful_result: Dict[str, Any]
) -> List[str]:
    """Suggest related actions the user might want to take next."""
    
    suggestions = []
    
    if intent == "analyze_sales_trends":
        suggestions.extend([
            "Would you like me to forecast future trends?",
            "Should I compare this to previous periods?",
            "Want to see which products drove these trends?"
        ])
        
    elif intent == "forecast_sales":
        suggestions.extend([
            "Should I check current inventory levels for this forecast?",
            "Would you like to see historical trends that led to this prediction?",
            "Want me to create a chart of the forecast?"
        ])
        
    elif intent == "analyze_product_performance":
        suggestions.extend([
            "Should I forecast performance for the top products?",
            "Would you like to see inventory levels for these products?",
            "Want to compare performance across different time periods?"
        ])
        
    elif intent == "view_inventory_status":
        suggestions.extend([
            "Should I analyze sales velocity for these items?",
            "Would you like forecasts to plan restocking?",
            "Want to see which products need immediate attention?"
        ])
        
    return suggestions[:3]  # Return top 3 suggestions

# Export functions
__all__ = [
    "handle_fallback_intent",
    "handle_clarification_request",
    "resolve_follow_up_context",
    "suggest_related_actions"
]
