"""
Period Comparison Tool for LangGraph
Dedicated tool for comparing metrics between different time periods
"""

from langchain_core.tools import tool
import requests
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

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
def compare_periods(
    current_period: str,
    comparison_period: str,
    metric: str = "revenue",
    product_id: Optional[str] = None,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compare metrics between different time periods.
    
    Args:
        current_period: Current analysis period (e.g., "this_month", "last_quarter")
        comparison_period: Period to compare against (e.g., "last_month", "previous_year")
        metric: Metric to compare (revenue, sales_volume, profit_margin)
        product_id: Specific product to compare
        category: Product category filter
    
    Returns:
        Comparison data with percentage changes and insights
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
            
        # Period comparison requires historical sales data which is not available in contract.md endpoints
        return {
            "error": True,
            "message": "Unable to connect to backend server - period comparison requires historical sales data",
            "endpoint": "No sales analytics endpoints available in contract.md",
            "suggestion": "Please ensure the inventory backend API is running on port 8000 and includes sales/analytics endpoints"
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Period comparison failed: {str(e)}",
            "tool": "compare_periods"
        }

@tool
def analyze_growth_drivers(
    time_period: str = "last_month",
    threshold: float = 10.0
) -> Dict[str, Any]:
    """
    Identify key factors driving growth or decline in sales.
    
    Args:
        time_period: Period to analyze for growth drivers
        threshold: Minimum growth percentage to consider significant
        
    Returns:
        Growth drivers analysis with contributing factors
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
            
        # Growth driver analysis requires sales and performance data which is not available in contract.md endpoints
        return {
            "error": True,
            "message": "Unable to connect to backend server - growth driver analysis requires sales and performance data",
            "endpoint": "No sales analytics endpoints available in contract.md",
            "suggestion": "Please ensure the inventory backend API is running on port 8000 and includes sales/analytics endpoints"
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Growth driver analysis failed: {str(e)}",
            "tool": "analyze_growth_drivers"
        }