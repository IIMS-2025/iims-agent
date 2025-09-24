#!/usr/bin/env python3
"""
LangGraph Runner Script
Executes the sales analytics flow and returns results
This script is called by the Node.js server to process user messages
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from dotenv import load_dotenv
load_dotenv()

# Import the LangGraph flows
from langgraph.flows.sales_analytics_flow import process_user_message
from langgraph.flows.react_analytics_flow import process_user_message_react  
from langgraph.flows.hybrid_analytics_flow import process_user_message_hybrid

async def main():
    """Main function to process user input and return response"""
    
    try:
        # Read input from command line arguments or stdin
        if len(sys.argv) > 1:
            # Input passed as command line argument
            input_data = json.loads(sys.argv[1])
        else:
            # Read from stdin
            input_json = sys.stdin.read()
            input_data = json.loads(input_json)
            
        # Extract required fields
        message = input_data.get("message", "")
        session_id = input_data.get("session_id", "default")
        conversation_history = input_data.get("context", {}).get("conversationHistory", [])
        session_context = input_data.get("context", {}).get("sessionContext", {})
        
        # Extract method preference (intent, react, auto)
        method = input_data.get("method", "auto")
        
        # Process through appropriate LangGraph flow
        if method == "react":
            result = await process_user_message_react(
                message=message,
                session_id=session_id,
                conversation_history=conversation_history,
                session_context=session_context
            )
        elif method == "intent":
            result = await process_user_message(
                message=message,
                session_id=session_id,
                conversation_history=conversation_history,
                session_context=session_context
            )
            # Add method indicator
            result["method"] = "intent"
        else:
            # Use hybrid approach with auto-selection
            result = await process_user_message_hybrid(
                message=message,
                session_id=session_id,
                conversation_history=conversation_history,
                session_context=session_context,
                method=method
            )
        
        # Return result as JSON
        print(json.dumps(result, indent=2))
        
    except json.JSONDecodeError as e:
        error_result = {
            "success": False,
            "response": "Invalid JSON input provided",
            "error": str(e),
            "intent": "error"
        }
        print(json.dumps(error_result))
        sys.exit(1)
        
    except Exception as e:
        error_result = {
            "success": False,
            "response": f"Processing failed: {str(e)}",
            "error": str(e),
            "intent": "error"
        }
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
