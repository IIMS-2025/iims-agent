"""
Sales Forecasting Tool for LangGraph
Generates sales predictions and demand forecasting
"""

from langchain_core.tools import tool
import requests
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json
import random

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
X_TENANT_ID = os.getenv("X_TENANT_ID", "11111111-1111-1111-1111-111111111111")

@tool
def forecast_sales(
    product_id: Optional[str] = None,
    product_name: Optional[str] = None,
    category: Optional[str] = None,
    forecast_days: int = 30,
    include_confidence: bool = True,
    include_inventory_impact: bool = True
) -> Dict[str, Any]:
    """
    Generate sales forecasts based on historical data and trends.
    
    Args:
        product_id: Specific product ID to forecast
        product_name: Product name to forecast (will resolve to ID)
        category: Product category to forecast
        forecast_days: Number of days to forecast (7, 30, 90)
        include_confidence: Include confidence intervals
        include_inventory_impact: Include inventory planning implications
    
    Returns:
        Forecast data with predictions and confidence levels
    """
    
    try:
        from .sales_analytics_tool import make_api_call
        
        # Get current inventory data for baseline
        inventory_data = make_api_call("/api/v1/inventory")
        
        if inventory_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to connect to backend server: {inventory_data.get('message')}",
                "endpoint": "/api/v1/inventory",
                "suggestion": "Please ensure the inventory backend API is running on port 8000"
            }
            
        # Backend returns: {"data": [{"inventory_items": [...], "summary": {...}}]}
        data_wrapper = inventory_data.get("data", [])
        if data_wrapper and len(data_wrapper) > 0:
            inventory_items = data_wrapper[0].get("inventory_items", [])
        else:
            inventory_items = []
        
        # Filter products based on criteria
        target_products = inventory_items
        
        if product_name:
            target_products = [
                item for item in inventory_items 
                if product_name.lower() in item.get("name", "").lower()
            ]
        elif product_id:
            target_products = [
                item for item in inventory_items 
                if item.get("id") == product_id
            ]
        elif category:
            target_products = [
                item for item in inventory_items 
                if item.get("category", "").lower() == category.lower()
            ]
            
        if not target_products:
            return {
                "error": True,
                "message": "No products found matching criteria",
                "criteria": {
                    "product_id": product_id,
                    "product_name": product_name,
                    "category": category
                }
            }
            
        # Sales forecasting requires historical sales data which is not available in contract.md endpoints
        return {
            "error": True,
            "message": "Unable to connect to backend server - sales forecasting requires historical sales data",
            "endpoint": "No sales analytics endpoints available in contract.md",
            "suggestion": "Please ensure the inventory backend API is running on port 8000 and includes sales/analytics endpoints"
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Forecasting failed: {str(e)}",
            "tool": "forecast_sales"
        }

@tool  
def analyze_seasonal_trends(
    product_category: str = "menu",
    months_back: int = 6
) -> Dict[str, Any]:
    """
    Analyze seasonal trends and patterns in sales data.
    
    Args:
        product_category: Category to analyze (menu, raw_material)
        months_back: How many months of history to analyze
        
    Returns:
        Seasonal analysis with patterns and predictions
    """
    
    try:
        # Seasonal analysis requires historical sales data which is not available in contract.md endpoints
        return {
            "error": True,
            "message": "Unable to connect to backend server - seasonal trend analysis requires historical sales data",
            "endpoint": "No sales analytics endpoints available in contract.md",
            "suggestion": "Please ensure the inventory backend API is running on port 8000 and includes sales/analytics endpoints"
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Seasonal analysis failed: {str(e)}",
            "tool": "analyze_seasonal_trends"
        }
