"""
Product Performance Analysis Tool for LangGraph
Dedicated tool for analyzing menu item and ingredient performance
"""

from langchain_core.tools import tool
import requests
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

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
def analyze_product_performance(
    time_period: str = "last_month",
    metric: str = "revenue",
    top_n: int = 10,
    category: Optional[str] = None,
    include_comparisons: bool = True
) -> Dict[str, Any]:
    """
    Analyze product performance metrics and rankings.
    
    Args:
        time_period: Analysis period (last_week, last_month, last_quarter)
        metric: Performance metric (revenue, quantity_sold, profit_margin)
        top_n: Number of top/bottom performers to return
        category: Filter by product category (menu, raw_material, sub_product)
        include_comparisons: Include period-over-period comparisons
    
    Returns:
        Product performance rankings and insights with actionable recommendations
    """
    
    try:
        # Get inventory data first to verify backend connectivity
        inventory_data = make_api_call("/api/v1/inventory")
        
        if inventory_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to connect to backend server: {inventory_data.get('message')}",
                "endpoint": "/api/v1/inventory",
                "suggestion": "Please ensure the inventory backend API is running on port 8000"
            }
            
        # Product performance analysis requires sales data which is not available in contract.md endpoints
        return {
            "error": True,
            "message": "Unable to connect to backend server - product performance analysis requires sales data",
            "endpoint": "No sales analytics endpoints available in contract.md",
            "suggestion": "Please ensure the inventory backend API is running on port 8000 and includes sales/analytics endpoints"
        }
            
    except Exception as e:
        return {
            "error": True,
            "message": f"Product performance analysis failed: {str(e)}",
            "tool": "analyze_product_performance"
        }

@tool
def get_product_ranking_by_category(
    metric: str = "revenue",
    time_period: str = "last_month"
) -> Dict[str, Any]:
    """
    Get product rankings grouped by category.
    
    Args:
        metric: Metric to rank by (revenue, quantity_sold, profit_margin)
        time_period: Period for analysis
        
    Returns:
        Product rankings organized by category
    """
    
    try:
        # Get inventory data first to verify backend connectivity
        inventory_data = make_api_call("/api/v1/inventory")
        
        if inventory_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to connect to backend server: {inventory_data.get('message')}",
                "endpoint": "/api/v1/inventory",
                "suggestion": "Please ensure the inventory backend API is running on port 8000"
            }
            
        # Product ranking requires sales data which is not available in contract.md endpoints
        return {
            "error": True,
            "message": "Unable to connect to backend server - product ranking requires sales data",
            "endpoint": "No sales analytics endpoints available in contract.md",
            "suggestion": "Please ensure the inventory backend API is running on port 8000 and includes sales/analytics endpoints"
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Category ranking failed: {str(e)}",
            "tool": "get_product_ranking_by_category"
        }