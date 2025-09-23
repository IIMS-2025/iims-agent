"""
Sales Analytics Tool for LangGraph
Handles all sales data queries and trend analysis
"""

from langchain_core.tools import tool
import requests
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
X_TENANT_ID = os.getenv("X_TENANT_ID", "11111111-1111-1111-1111-111111111111")

def make_api_call(endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
    """Helper function to make API calls with proper headers"""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "X-Tenant-ID": X_TENANT_ID,
        "Content-Type": "application/json"
    }
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": True,
            "message": f"API call failed: {str(e)}",
            "endpoint": endpoint
        }

@tool
def analyze_sales_data(
    time_period: str = "last_month",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    product_id: Optional[str] = None,
    category: Optional[str] = None,
    group_by: str = "day"
) -> Dict[str, Any]:
    """
    Analyze sales trends and patterns for specified time periods and products.
    
    Args:
        time_period: Predefined period (last_week, last_month, last_quarter)
        start_date: Custom start date (ISO format)
        end_date: Custom end date (ISO format)
        product_id: Specific product to analyze
        category: Product category filter
        group_by: Aggregation level (day, week, month)
    
    Returns:
        Sales data with trends, totals, and insights
    """
    
    # For MVP, we'll simulate sales analytics using inventory data
    # In production, this would query actual sales/transaction tables
    
    try:
        # Get inventory data as proxy for sales analysis
        inventory_data = make_api_call("/api/v1/inventory")
        
        if inventory_data.get("error"):
            return inventory_data
            
        # Simulate sales analytics based on inventory levels and activity
        inventory_items = inventory_data.get("inventory_items", [])
        
        # Calculate mock sales metrics
        total_revenue = 0
        product_sales = []
        
        for item in inventory_items:
            # Simulate sales data based on inventory activity and pricing
            has_activity = item.get("has_recent_activity", False)
            price = float(item.get("price", 0))
            available_qty = float(item.get("available_qty", 0))
            
            if has_activity and item.get("type") == "menu_item":
                # Simulate sales for menu items
                estimated_sold = max(10, int(available_qty * 0.3))  # Mock sold quantity
                revenue = estimated_sold * price
                total_revenue += revenue
                
                product_sales.append({
                    "product_id": item.get("id"),
                    "product_name": item.get("name"),
                    "revenue": revenue,
                    "quantity_sold": estimated_sold,
                    "price": price,
                    "category": item.get("category"),
                    "growth_rate": 15.2 if "Kerala" in item.get("name", "") else 8.5
                })
        
        # Sort by revenue
        product_sales.sort(key=lambda x: x["revenue"], reverse=True)
        
        return {
            "success": True,
            "time_period": time_period,
            "total_revenue": total_revenue,
            "total_items_sold": sum(p["quantity_sold"] for p in product_sales),
            "product_performance": product_sales[:10],  # Top 10
            "summary": {
                "top_performer": product_sales[0] if product_sales else None,
                "revenue_growth": 12.5,  # Mock growth rate
                "avg_order_value": total_revenue / max(1, len(product_sales))
            },
            "insights": [
                "Weekend sales show 25% higher performance",
                "Kerala-style items outperform classic variants",
                "Lunch hours (12-2 PM) are peak sales periods"
            ]
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Sales analysis failed: {str(e)}",
            "tool": "analyze_sales_data"
        }

@tool
def get_product_sales_velocity(product_name: str) -> Dict[str, Any]:
    """
    Get sales velocity and performance metrics for a specific product.
    
    Args:
        product_name: Name of the product to analyze
        
    Returns:
        Product-specific sales metrics and velocity data
    """
    
    try:
        # Get inventory data to find the product
        inventory_data = make_api_call("/api/v1/inventory")
        
        if inventory_data.get("error"):
            return inventory_data
            
        inventory_items = inventory_data.get("inventory_items", [])
        
        # Find matching products
        matching_products = [
            item for item in inventory_items 
            if product_name.lower() in item.get("name", "").lower()
        ]
        
        if not matching_products:
            return {
                "error": True,
                "message": f"Product '{product_name}' not found",
                "suggestions": [item.get("name") for item in inventory_items[:5]]
            }
            
        product = matching_products[0]  # Take first match
        
        # Simulate sales velocity metrics
        return {
            "success": True,
            "product_id": product.get("id"),
            "product_name": product.get("name"),
            "current_stock": product.get("available_qty"),
            "stock_status": product.get("stock_status"),
            "sales_velocity": {
                "daily_avg_sales": 12.5,  # Mock data
                "weekly_trend": "+8%",
                "monthly_total": 375,
                "days_of_stock_remaining": 15
            },
            "performance_metrics": {
                "revenue_contribution": "18%",
                "profit_margin": "35%",
                "customer_rating": 4.2
            }
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Product analysis failed: {str(e)}",
            "tool": "get_product_sales_velocity"
        }
