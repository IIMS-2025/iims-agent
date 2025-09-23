#!/usr/bin/env python3
"""
Test runner for the sales analytics tools
Run this to validate tool functionality before server integration
"""

import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Import tools for testing
from langgraph.tools.sales_analytics_tool import analyze_sales_data, get_product_sales_velocity
from langgraph.tools.forecasting_tool import forecast_sales, analyze_seasonal_trends
from langgraph.tools.inventory_tool import get_inventory_status, check_stock_alerts
from langgraph.tools.comparison_tool import compare_periods, analyze_growth_drivers
from langgraph.tools.chart_data_tool import generate_chart_data, create_dashboard_summary

async def test_sales_analytics_tools():
    """Test all the sales analytics tools"""
    
    print("🧪 Testing Sales Analytics Tools\n")
    print("=" * 50)
    
    # Test 1: Sales Data Analysis
    print("\n📊 Test 1: Sales Data Analysis")
    print("-" * 30)
    result = await analyze_sales_data.ainvoke({"time_period": "last_month"})
    print(f"✅ Sales Analysis: {result.get('success', False)}")
    if result.get('success'):
        print(f"   Total Revenue: ₹{result.get('total_revenue', 0):,.2f}")
        print(f"   Items Sold: {result.get('total_items_sold', 0)}")
        print(f"   Growth Rate: {result.get('summary', {}).get('revenue_growth', 0)}%")
    
    # Test 2: Sales Forecasting
    print("\n🔮 Test 2: Sales Forecasting")
    print("-" * 30)
    result = await forecast_sales.ainvoke({"product_name": "Kerala Burger", "forecast_days": 30})
    print(f"✅ Forecasting: {result.get('success', False)}")
    if result.get('success') and result.get('forecasts'):
        forecast = result['forecasts'][0]
        print(f"   Product: {forecast.get('product_name')}")
        print(f"   Predicted Revenue: ₹{forecast.get('predicted_revenue', 0):,.2f}")
        print(f"   Growth Factor: {forecast.get('growth_factor', 0)}%")
    
    # Test 3: Inventory Status
    print("\n📦 Test 3: Inventory Status")
    print("-" * 30)
    result = await get_inventory_status.ainvoke({"include_sales_context": True})
    print(f"✅ Inventory Status: {result.get('success', False)}")
    if result.get('success'):
        items = result.get('inventory_items', [])
        print(f"   Total Items: {len(items)}")
        print(f"   Low Stock Items: {result.get('summary', {}).get('total_low_stock', 0)}")
        
        # Show a few items with sales context
        for item in items[:3]:
            sales_context = item.get('sales_context', {})
            print(f"   - {item.get('name')}: {item.get('available_qty')} {item.get('unit')} ({sales_context.get('sales_velocity', 'Unknown')} velocity)")
    
    # Test 4: Period Comparison
    print("\n📈 Test 4: Period Comparison")
    print("-" * 30)
    result = await compare_periods.ainvoke({
        "current_period": "this_month",
        "comparison_period": "last_month",
        "metric": "revenue"
    })
    print(f"✅ Period Comparison: {result.get('success', False)}")
    if result.get('success'):
        comparison = result.get('comparison', {})
        changes = result.get('changes', {})
        print(f"   Current: ₹{comparison.get('current_period', {}).get('value', 0):,.2f}")
        print(f"   Previous: ₹{comparison.get('comparison_period', {}).get('value', 0):,.2f}")
        print(f"   Change: {changes.get('percentage_change', 0):+.1f}% ({changes.get('trend', 'Unknown')})")
    
    # Test 5: Chart Data Generation
    print("\n📊 Test 5: Chart Data Generation")
    print("-" * 30)
    result = await generate_chart_data.ainvoke({
        "chart_type": "line",
        "data_source": "sales",
        "time_period": "last_month"
    })
    print(f"✅ Chart Data: {result.get('success', False)}")
    if result.get('success'):
        chart_config = result.get('chart_config', {})
        print(f"   Chart Type: {chart_config.get('type')}")
        print(f"   Title: {chart_config.get('title')}")
        datasets = chart_config.get('datasets', [])
        if datasets:
            print(f"   Data Points: {len(datasets[0].get('data', []))}")
    
    # Test 6: Stock Alerts
    print("\n⚠️  Test 6: Stock Alerts")
    print("-" * 30)
    result = await check_stock_alerts.ainvoke({})
    print(f"✅ Stock Alerts: {result.get('success', False)}")
    if result.get('success'):
        alerts = result.get('alerts', [])
        print(f"   Total Alerts: {len(alerts)}")
        print(f"   Critical: {result.get('critical_count', 0)}")
        
        for alert in alerts[:3]:  # Show first 3
            print(f"   - {alert.get('product_name')}: {alert.get('alert_type')} ({alert.get('severity')})")
    
    print("\n" + "=" * 50)
    print("🎉 Tool testing completed!")
    
    # Test API connectivity
    print("\n🌐 Testing API Connectivity")
    print("-" * 30)
    
    if not os.getenv("BASE_URL"):
        print("⚠️  BASE_URL not set - using default http://localhost:8000")
    if not os.getenv("X_TENANT_ID"):
        print("⚠️  X_TENANT_ID not set - using default test tenant")
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set - AI responses will be limited")
        
    print(f"📡 API Base URL: {os.getenv('BASE_URL', 'http://localhost:8000')}")
    print(f"🏢 Tenant ID: {os.getenv('X_TENANT_ID', '11111111-1111-1111-1111-111111111111')[:8]}...")

if __name__ == "__main__":
    asyncio.run(test_sales_analytics_tools())
