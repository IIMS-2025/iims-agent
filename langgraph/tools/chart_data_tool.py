"""
Chart Data Generation Tool for LangGraph
Generates data structures for chart visualizations
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
        # Get inventory data first to verify backend connectivity
        inventory_data = make_api_call("/api/v1/inventory")
        
        if inventory_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to connect to backend server: {inventory_data.get('message')}",
                "endpoint": "/api/v1/inventory",
                "suggestion": "Please ensure the inventory backend API is running on port 8000"
            }
            
        # Chart data generation requires sales/analytics data which is not available in contract.md endpoints
        return {
            "error": True,
            "message": "Unable to connect to backend server - chart generation requires sales analytics data",
            "endpoint": "No sales analytics endpoints available in contract.md",
            "suggestion": "Please ensure the inventory backend API is running on port 8000 and includes sales/analytics endpoints"
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Chart generation failed: {str(e)}",
            "tool": "generate_chart_data"
        }

@tool
def create_dashboard_summary(
    include_charts: bool = True,
    time_period: str = "last_month"
) -> Dict[str, Any]:
    """
    Create a comprehensive dashboard summary with key metrics and visualizations.
    
    Args:
        include_charts: Whether to include chart data in the response
        time_period: Time period for dashboard data
        
    Returns:
        Dashboard summary with metrics, insights, and chart configurations
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
            
        # Dashboard creation requires comprehensive sales and analytics data which is not available in contract.md endpoints
        return {
            "error": True,
            "message": "Unable to connect to backend server - dashboard creation requires comprehensive sales and analytics data",
            "endpoint": "No sales analytics endpoints available in contract.md",
            "suggestion": "Please ensure the inventory backend API is running on port 8000 and includes sales/analytics endpoints"
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Dashboard creation failed: {str(e)}",
            "tool": "create_dashboard_summary"
        }