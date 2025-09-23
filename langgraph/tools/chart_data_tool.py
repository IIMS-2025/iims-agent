"""
Chart Data Generation Tool for LangGraph
Generates data formatted for frontend chart visualization
"""

from langchain_core.tools import tool
import requests
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import random

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
X_TENANT_ID = os.getenv("X_TENANT_ID", "11111111-1111-1111-1111-111111111111")

@tool
def generate_chart_data(
    chart_type: str,
    data_source: str,
    time_period: str = "last_month",
    product_filter: Optional[str] = None,
    group_by: str = "day"
) -> Dict[str, Any]:
    """
    Generate data formatted for chart visualization.
    
    Args:
        chart_type: Type of chart (line, bar, pie, trend)
        data_source: Data to chart (sales, inventory, forecasts, performance)
        time_period: Time range for data
        product_filter: Filter by product or category
        group_by: Aggregation level (day, week, month, product)
    
    Returns:
        Chart-ready data with labels, values, and formatting
    """
    
    try:
        # Generate mock chart data based on chart type and data source
        chart_data = {}
        
        if chart_type == "line" and data_source == "sales":
            # Daily sales trend line chart
            dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30, 0, -1)]
            revenues = [random.uniform(2000, 8000) for _ in dates]
            
            chart_data = {
                "type": "line",
                "title": f"Sales Trends - {time_period.replace('_', ' ').title()}",
                "labels": dates,
                "datasets": [{
                    "label": "Daily Revenue (₹)",
                    "data": [round(r, 2) for r in revenues],
                    "borderColor": "#3b82f6",
                    "backgroundColor": "rgba(59, 130, 246, 0.1)",
                    "tension": 0.4
                }],
                "insights": [
                    "Revenue shows upward trend with weekend peaks",
                    "Average daily revenue: ₹" + str(round(sum(revenues) / len(revenues), 2)),
                    "Highest performing day: " + dates[revenues.index(max(revenues))]
                ]
            }
            
        elif chart_type == "bar" and data_source == "performance":
            # Product performance bar chart
            products = ["Kerala Burger", "Chicken Burger", "Fish Burger", "Classic Combo", "Seafood Combo"]
            revenues = [random.uniform(15000, 35000) for _ in products]
            
            chart_data = {
                "type": "bar",
                "title": "Product Performance Comparison",
                "labels": products,
                "datasets": [{
                    "label": "Revenue (₹)",
                    "data": [round(r, 2) for r in revenues],
                    "backgroundColor": [
                        "#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6"
                    ]
                }],
                "insights": [
                    f"Top performer: {products[revenues.index(max(revenues))]}",
                    f"Needs attention: {products[revenues.index(min(revenues))]}",
                    "Kerala items consistently outperform classic variants"
                ]
            }
            
        elif chart_type == "pie" and data_source == "inventory":
            # Stock status distribution pie chart
            status_data = {
                "In Stock": 60,
                "Low Stock": 25,
                "Out of Stock": 10,
                "Expiring Soon": 5
            }
            
            chart_data = {
                "type": "pie",
                "title": "Current Stock Status Distribution",
                "labels": list(status_data.keys()),
                "datasets": [{
                    "data": list(status_data.values()),
                    "backgroundColor": [
                        "#10b981",  # Green for in stock
                        "#f59e0b",  # Orange for low stock
                        "#ef4444",  # Red for out of stock
                        "#8b5cf6"   # Purple for expiring
                    ]
                }],
                "insights": [
                    "60% of inventory is at healthy levels",
                    "25% requires attention (low stock)",
                    "15% needs immediate action (out of stock/expiring)"
                ]
            }
            
        elif chart_type == "trend" and data_source == "forecasts":
            # Forecast trend chart
            dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 31)]
            forecasts = []
            base_value = 5000
            
            for i, date in enumerate(dates):
                # Simulate trending forecast
                trend_factor = 1 + (i * 0.01)  # 1% daily growth
                seasonal_factor = 1.1 if i % 7 in [5, 6] else 1.0  # Weekend boost
                value = base_value * trend_factor * seasonal_factor + random.uniform(-500, 500)
                forecasts.append(round(value, 2))
                
            chart_data = {
                "type": "line",
                "title": "30-Day Sales Forecast",
                "labels": dates,
                "datasets": [{
                    "label": "Predicted Revenue (₹)",
                    "data": forecasts,
                    "borderColor": "#8b5cf6",
                    "backgroundColor": "rgba(139, 92, 246, 0.1)",
                    "borderDash": [5, 5],
                    "tension": 0.4
                }],
                "insights": [
                    "Steady growth trend predicted for next 30 days",
                    "Weekend peaks expected throughout the period",
                    "Total predicted revenue: ₹" + str(round(sum(forecasts), 2))
                ]
            }
            
        else:
            # Default chart structure
            chart_data = {
                "type": chart_type,
                "title": f"{data_source.title()} {chart_type.title()} Chart",
                "labels": ["No Data"],
                "datasets": [{
                    "label": "Data",
                    "data": [0],
                    "backgroundColor": "#6b7280"
                }],
                "insights": [
                    f"Chart type '{chart_type}' with data source '{data_source}' is not yet implemented",
                    "Available combinations: line+sales, bar+performance, pie+inventory, trend+forecasts"
                ]
            }
            
        return {
            "success": True,
            "chart_config": chart_data,
            "metadata": {
                "chart_type": chart_type,
                "data_source": data_source,
                "time_period": time_period,
                "product_filter": product_filter,
                "group_by": group_by,
                "generated_at": datetime.now().isoformat()
            },
            "frontend_integration": {
                "library": "Chart.js",
                "component_props": {
                    "type": chart_data["type"],
                    "data": {
                        "labels": chart_data["labels"],
                        "datasets": chart_data["datasets"]
                    },
                    "options": {
                        "responsive": True,
                        "plugins": {
                            "title": {
                                "display": True,
                                "text": chart_data["title"]
                            }
                        }
                    }
                }
            }
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Chart data generation failed: {str(e)}",
            "tool": "generate_chart_data"
        }

@tool
def create_dashboard_summary(
    time_period: str = "this_month"
) -> Dict[str, Any]:
    """
    Create a comprehensive dashboard summary with multiple chart data sets.
    
    Args:
        time_period: Period for dashboard data
        
    Returns:
        Multiple chart datasets for a complete dashboard view
    """
    
    try:
        # Generate multiple chart datasets for dashboard
        charts = []
        
        # 1. Revenue trend
        revenue_chart = generate_chart_data("line", "sales", time_period)
        if revenue_chart.get("success"):
            charts.append({
                "id": "revenue_trend",
                "title": "Revenue Trends",
                "chart_data": revenue_chart["chart_config"],
                "size": "large"
            })
            
        # 2. Product performance
        performance_chart = generate_chart_data("bar", "performance", time_period)
        if performance_chart.get("success"):
            charts.append({
                "id": "product_performance",
                "title": "Product Performance",
                "chart_data": performance_chart["chart_config"],
                "size": "medium"
            })
            
        # 3. Stock status
        inventory_chart = generate_chart_data("pie", "inventory", time_period)
        if inventory_chart.get("success"):
            charts.append({
                "id": "stock_status",
                "title": "Stock Status",
                "chart_data": inventory_chart["chart_config"],
                "size": "small"
            })
            
        # Summary metrics
        summary_metrics = {
            "total_revenue": random.uniform(80000, 120000),
            "revenue_growth": random.uniform(5, 25),
            "top_product": "Kerala Burger",
            "inventory_health": "Good",
            "alerts_count": random.randint(2, 8)
        }
        
        return {
            "success": True,
            "dashboard": {
                "period": time_period,
                "charts": charts,
                "summary_metrics": {
                    "total_revenue": f"₹{summary_metrics['total_revenue']:,.0f}",
                    "revenue_growth": f"+{summary_metrics['revenue_growth']:.1f}%",
                    "top_product": summary_metrics['top_product'],
                    "inventory_health": summary_metrics['inventory_health'],
                    "active_alerts": summary_metrics['alerts_count']
                },
                "quick_insights": [
                    "📈 Revenue trending upward with strong weekend performance",
                    "🏆 Kerala Burger continues to lead product performance",
                    "⚠️ Monitor inventory levels for high-velocity items",
                    "💡 Consider expanding Kerala-style menu offerings"
                ]
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Dashboard summary creation failed: {str(e)}",
            "tool": "create_dashboard_summary"
        }
