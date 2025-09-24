"""
Hybrid Analytics Flow - Choose between Intent-based and ReAct systems
Allows comparison and gradual migration between the two approaches
"""

import os
from typing import Dict, Any, List, Optional, Literal
from .sales_analytics_flow import process_user_message as process_intent_based
from .react_analytics_flow import process_user_message_react

async def process_user_message_hybrid(
    message: str,
    session_id: str,
    conversation_history: List[Dict[str, Any]] = None,
    session_context: Dict[str, Any] = None,
    method: Literal["intent", "react", "auto"] = "auto"
) -> Dict[str, Any]:
    """
    Process user message using either intent-based or ReAct approach
    
    Args:
        message: User's input message
        session_id: Session identifier  
        conversation_history: Previous conversation messages
        session_context: Previous session context
        method: Which method to use ("intent", "react", "auto")
        
    Returns:
        Response with method indicator and processing results
    """
    
    # Auto-selection logic (can be customized)
    if method == "auto":
        # Use ReAct for complex questions, intent-based for simple ones
        message_lower = message.lower()
        
        # Complex indicators that benefit from ReAct reasoning
        complex_indicators = [
            "why", "how", "explain", "analyze why", "what caused", 
            "multiple", "compare and", "both", "also show",
            "comprehensive", "detailed analysis", "investigation"
        ]
        
        # Simple direct requests that work well with intent-based
        simple_indicators = [
            "show me", "get", "list", "status", "current", 
            "last month", "forecast", "inventory"
        ]
        
        if any(indicator in message_lower for indicator in complex_indicators):
            method = "react"
        elif any(indicator in message_lower for indicator in simple_indicators):
            method = "intent"
        else:
            # Default to ReAct for ambiguous cases
            method = "react"
    
    try:
        if method == "react":
            result = await process_user_message_react(
                message, session_id, conversation_history, session_context
            )
        else:
            result = await process_intent_based(
                message, session_id, conversation_history, session_context
            )
            # Add method indicator to intent-based response
            result["method"] = "intent"
            
        return result
        
    except Exception as e:
        # Fallback to the other method if one fails
        fallback_method = "intent" if method == "react" else "react"
        
        try:
            if fallback_method == "react":
                result = await process_user_message_react(
                    message, session_id, conversation_history, session_context
                )
            else:
                result = await process_intent_based(
                    message, session_id, conversation_history, session_context
                )
                result["method"] = "intent"
                
            result["fallback_used"] = True
            result["original_method"] = method
            result["fallback_reason"] = str(e)
            
            return result
            
        except Exception as fallback_error:
            return {
                "success": False,
                "response": f"Both processing methods failed. Original: {str(e)}, Fallback: {str(fallback_error)}",
                "method": "error",
                "error": str(e),
                "session_context": session_context or {}
            }

# Export function
__all__ = ["process_user_message_hybrid"]
