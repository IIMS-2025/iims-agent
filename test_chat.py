#!/usr/bin/env python3
"""
Interactive test script for the sales analytics assistant
Tests the complete flow from user input to AI response
"""

import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Set default environment variables for testing
os.environ.setdefault("BASE_URL", "http://localhost:8000")
os.environ.setdefault("X_TENANT_ID", "11111111-1111-1111-1111-111111111111")
os.environ.setdefault("OPENAI_API_KEY", "test-key")

async def test_conversation_flow():
    """Test a complete conversation flow"""
    
    print("🤖 Sales Analytics Assistant - Interactive Test")
    print("=" * 50)
    
    # Import the flow after setting environment
    try:
        from langgraph.flows.sales_analytics_flow import process_user_message
        
        # Test scenarios
        test_scenarios = [
            {
                "name": "Sales Trends Analysis",
                "message": "Show me sales trends for last month",
                "expected_intent": "analyze_sales_trends"
            },
            {
                "name": "Product Performance",
                "message": "Which menu items are performing best?",
                "expected_intent": "analyze_product_performance"
            },
            {
                "name": "Sales Forecasting", 
                "message": "Predict Kerala Burger sales for next 30 days",
                "expected_intent": "forecast_sales"
            },
            {
                "name": "Period Comparison",
                "message": "Compare this month vs last month revenue",
                "expected_intent": "compare_periods"
            },
            {
                "name": "Inventory Status",
                "message": "What inventory needs attention?",
                "expected_intent": "view_inventory_status"
            }
        ]
        
        session_id = "test_session_123"
        conversation_history = []
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n🧪 Test {i}: {scenario['name']}")
            print("-" * 40)
            print(f"👤 User: {scenario['message']}")
            
            try:
                result = await process_user_message(
                    message=scenario['message'],
                    session_id=session_id,
                    conversation_history=conversation_history
                )
                
                if result.get('success'):
                    response = result.get('response', '')
                    intent = result.get('intent', '')
                    tools_used = [tr.get('tool') for tr in result.get('tool_results', [])]
                    
                    print(f"🤖 Assistant: {response[:100]}{'...' if len(response) > 100 else ''}")
                    print(f"🎯 Intent: {intent}")
                    print(f"🔧 Tools Used: {', '.join(tools_used) if tools_used else 'None'}")
                    
                    # Check intent matching
                    if intent == scenario['expected_intent']:
                        print("✅ Intent classification: PASSED")
                    else:
                        print(f"❌ Intent classification: FAILED (expected {scenario['expected_intent']}, got {intent})")
                    
                    # Add to conversation history for context
                    conversation_history.extend([
                        {"role": "user", "content": scenario['message']},
                        {"role": "assistant", "content": response}
                    ])
                    
                else:
                    print(f"❌ Error: {result.get('response', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Exception: {str(e)}")
                
        print("\n" + "=" * 50)
        print("🏁 Conversation flow test completed!")
        
        # Test follow-up context
        print("\n🔄 Testing Follow-up Context")
        print("-" * 40)
        followup_message = "What about the forecast for that product?"
        print(f"👤 User: {followup_message}")
        
        try:
            result = await process_user_message(
                message=followup_message,
                session_id=session_id,
                conversation_history=conversation_history
            )
            
            if result.get('success'):
                print(f"🤖 Assistant: {result.get('response', '')[:100]}...")
                print("✅ Follow-up context handling: PASSED")
            else:
                print("❌ Follow-up context handling: FAILED")
                
        except Exception as e:
            print(f"❌ Follow-up test exception: {str(e)}")
            
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("💡 Make sure all dependencies are installed in the virtual environment")
        print("   Run: source venv/bin/activate && pip install -r requirements.txt")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

async def test_individual_tools():
    """Test individual tools directly"""
    
    print("\n🔧 Testing Individual Tools")
    print("=" * 50)
    
    try:
        from langgraph.tools.sales_analytics_tool import analyze_sales_data
        from langgraph.tools.inventory_tool import get_inventory_status
        
        # Test sales analytics tool
        print("\n📊 Testing Sales Analytics Tool...")
        result = analyze_sales_data(time_period="last_month")
        print(f"Result: {result.get('success', False)}")
        
        # Test inventory tool
        print("\n📦 Testing Inventory Tool...")
        result = get_inventory_status(filter_status="low_stock")
        print(f"Result: {result.get('success', False)}")
        
        print("✅ Individual tool tests completed!")
        
    except Exception as e:
        print(f"❌ Tool test failed: {str(e)}")

async def main():
    """Main test function"""
    
    print("🧪 IIMS Sales Analytics Assistant - Test Suite")
    print("📅 " + "=" * 48)
    
    # Check environment
    print("\n🔍 Environment Check:")
    print(f"   BASE_URL: {os.getenv('BASE_URL', 'Not set')}")
    print(f"   X_TENANT_ID: {os.getenv('X_TENANT_ID', 'Not set')[:8]}...")
    print(f"   OPENAI_API_KEY: {'Set' if os.getenv('OPENAI_API_KEY') else 'Not set'}")
    
    # Run tests
    await test_individual_tools()
    await test_conversation_flow()
    
    print("\n🎯 All tests completed!")
    print("\n💡 Next steps:")
    print("   1. Set your OPENAI_API_KEY in .env file")
    print("   2. Start the inventory backend API on http://localhost:8000")
    print("   3. Run: ./start.sh to start the ChatGPT-like server")
    print("   4. Test with: curl -X POST http://localhost:3000/chat -d '{\"message\":\"Show sales trends\"}'")

if __name__ == "__main__":
    asyncio.run(main())
