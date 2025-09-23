"""
Intent Extraction Node for LangGraph
Classifies user intent from natural language for sales analytics
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import os
import json
import re
from typing import Dict, Any

# Initialize LLM
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    temperature=0.3,  # Lower temperature for more consistent intent classification
    api_key=os.getenv("OPENAI_API_KEY")
)

def extract_intent_from_message(
    user_message: str,
    conversation_history: list = None
) -> Dict[str, Any]:
    """
    Extract user intent and confidence score from natural language message.
    
    Args:
        user_message: The user's input message
        conversation_history: Previous conversation for context
        
    Returns:
        Intent classification with confidence score and reasoning
    """
    
    conversation_context = ""
    if conversation_history:
        recent_messages = conversation_history[-3:]  # Last 3 messages for context
        conversation_context = f"\n\nRecent conversation context:\n{json.dumps(recent_messages, indent=2)}"
    
    intent_prompt = f"""
    You are an intent classifier for a sales analytics assistant at Kochi Burger Junction.
    
    Analyze this user message and classify the intent with high precision.
    
    User message: "{user_message}"
    {conversation_context}
    
    SUPPORTED INTENTS:
    
    1. analyze_sales_trends - Questions about sales patterns, trends, performance over time
       Examples: "Show sales trends", "How are sales performing?", "Revenue patterns"
       
    2. forecast_sales - Requests for sales predictions, demand forecasting  
       Examples: "Predict next month", "Forecast Kerala Burger sales", "What will sales be?"
       
    3. view_inventory_status - Questions about current stock levels, inventory health
       Examples: "Stock levels", "What's low on stock?", "Inventory status"
       
    4. analyze_product_performance - Product performance comparisons, rankings
       Examples: "Best selling items", "Which products perform best?", "Product rankings"
       
    5. compare_periods - Comparing metrics between different time periods
       Examples: "This month vs last month", "Compare revenue", "Year over year"
       
    6. view_specific_metrics - Specific revenue, profit, or performance questions
       Examples: "Kerala Burger revenue", "Profit margins", "Specific product metrics"
       
    7. generate_report - Requests for reports or comprehensive summaries
       Examples: "Create report", "Weekly summary", "Performance report"
       
    8. create_chart - Requests for charts, graphs, or visual data
       Examples: "Show me a chart", "Graph the data", "Visualize trends"
       
    9. update_stock_single - Basic inventory management operations
       Examples: "Add 20 kg tomatoes", "Update stock", "Increase inventory"
       
    10. help - General help or capability questions
        Examples: "What can you do?", "Help me", "Show examples"
        
    11. clarify - Ambiguous or incomplete requests needing clarification
        Use when: Request is unclear, missing critical parameters, or could mean multiple things
        
    12. fallback - Unrecognized intent or out-of-scope requests
        Use when: Request doesn't match any supported intents
    
    CLASSIFICATION RULES:
    - If user references previous conversation context (like "that product", "for that"), consider conversation history
    - Prioritize specific intents over general ones
    - If multiple intents possible, choose the most specific one
    - If truly ambiguous, use "clarify"
    - Confidence should be 0.9+ for clear matches, 0.7+ for good matches, below 0.7 for unclear
    
    Return ONLY valid JSON:
    {{
        "intent": "exact_intent_name",
        "confidence": 0.95,
        "reasoning": "Brief explanation of why this intent was chosen",
        "ambiguity_flags": ["any_ambiguous_aspects"],
        "context_used": true/false
    }}
    """
    
    try:
        if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your-openai-api-key-here":
            # Fallback to simple rule-based classification if no OpenAI key
            return classify_intent_fallback(user_message)
            
        response = llm.invoke([HumanMessage(content=intent_prompt)])
        result_text = response.content
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            intent_data = json.loads(json_match.group())
            
            # Validate intent
            supported_intents = [
                "analyze_sales_trends", "forecast_sales", "view_inventory_status",
                "analyze_product_performance", "compare_periods", "view_specific_metrics",
                "generate_report", "create_chart", "update_stock_single", 
                "help", "clarify", "fallback"
            ]
            
            if intent_data.get("intent") not in supported_intents:
                intent_data["intent"] = "fallback"
                intent_data["confidence"] = 0.5
                intent_data["reasoning"] = "Intent not in supported list, defaulting to fallback"
                
            return intent_data
        else:
            # Fallback if JSON parsing fails
            return classify_intent_fallback(user_message)
            
    except Exception as e:
        return {
            "intent": "fallback",
            "confidence": 0.3,
            "reasoning": f"Intent extraction failed: {str(e)}",
            "error": str(e)
        }

def classify_intent_fallback(user_message: str) -> Dict[str, Any]:
    """
    Fallback rule-based intent classification when OpenAI is not available.
    """
    
    message_lower = user_message.lower()
    
    # Rule-based classification
    if any(word in message_lower for word in ["trend", "trending", "pattern", "performance over time"]):
        return {
            "intent": "analyze_sales_trends",
            "confidence": 0.8,
            "reasoning": "Contains trend/pattern keywords",
            "method": "rule_based"
        }
    elif any(word in message_lower for word in ["predict", "forecast", "future", "next month", "coming"]):
        return {
            "intent": "forecast_sales", 
            "confidence": 0.8,
            "reasoning": "Contains prediction/forecasting keywords",
            "method": "rule_based"
        }
    elif any(word in message_lower for word in ["best", "top", "worst", "rank", "perform", "selling"]):
        return {
            "intent": "analyze_product_performance",
            "confidence": 0.8, 
            "reasoning": "Contains performance ranking keywords",
            "method": "rule_based"
        }
    elif any(word in message_lower for word in ["compare", "vs", "versus", "difference", "against"]):
        return {
            "intent": "compare_periods",
            "confidence": 0.8,
            "reasoning": "Contains comparison keywords", 
            "method": "rule_based"
        }
    elif any(word in message_lower for word in ["stock", "inventory", "level", "available"]):
        return {
            "intent": "view_inventory_status",
            "confidence": 0.8,
            "reasoning": "Contains inventory keywords",
            "method": "rule_based"
        }
    elif any(word in message_lower for word in ["report", "summary", "overview"]):
        return {
            "intent": "generate_report", 
            "confidence": 0.8,
            "reasoning": "Contains reporting keywords",
            "method": "rule_based"
        }
    elif any(word in message_lower for word in ["chart", "graph", "visualize", "plot"]):
        return {
            "intent": "create_chart",
            "confidence": 0.8, 
            "reasoning": "Contains visualization keywords",
            "method": "rule_based"
        }
    elif any(word in message_lower for word in ["add", "update", "increase", "adjust"]) and any(word in message_lower for word in ["kg", "pcs", "ml", "stock"]):
        return {
            "intent": "update_stock_single",
            "confidence": 0.7,
            "reasoning": "Contains stock update keywords with quantities",
            "method": "rule_based"
        }
    elif any(word in message_lower for word in ["help", "what can", "capabilities", "examples"]):
        return {
            "intent": "help",
            "confidence": 0.9,
            "reasoning": "Clear help request",
            "method": "rule_based"
        }
    else:
        return {
            "intent": "fallback",
            "confidence": 0.6,
            "reasoning": "No clear intent pattern matched",
            "method": "rule_based"
        }
