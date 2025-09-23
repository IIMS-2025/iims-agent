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

def check_backend_health() -> Dict[str, Any]:
    """Check if the backend API is available using the health endpoint from contract.md"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/healthz", timeout=5)
        if response.status_code == 200:
            return {"available": True, "status": response.json()}
        else:
            return {"available": False, "status_code": response.status_code}
    except Exception as e:
        return {"available": False, "error": str(e)}


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
    
    # Use inventory data from contract.md endpoints to simulate sales analytics
    # Real sales analytics would use dedicated sales endpoints (not in current contract)
    
    try:
        # Call the actual inventory endpoint from contract.md
        inventory_data = make_api_call("/api/v1/inventory")
        
        if inventory_data.get("error"):
            # Backend not available - throw error
            return {
                "error": True,
                "message": f"Unable to connect to backend server: {inventory_data.get('message')}",
                "endpoint": "/api/v1/inventory",
                "suggestion": "Please ensure the inventory backend API is running on port 8000"
            }
            
        # Sales analytics requires dedicated sales endpoints which are not available in contract.md
        return {
            "error": True,
            "message": "Unable to connect to backend server - sales analytics requires dedicated sales endpoints",
            "endpoint": "No sales analytics endpoints available in contract.md",
            "suggestion": "Please ensure the inventory backend API is running on port 8000 and includes sales/analytics endpoints"
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
            
        # Sales velocity analysis requires dedicated sales endpoints which are not available in contract.md
        return {
            "error": True,
            "message": "Unable to connect to backend server - sales velocity analysis requires dedicated sales endpoints",
            "endpoint": "No sales analytics endpoints available in contract.md", 
            "suggestion": "Please ensure the inventory backend API is running on port 8000 and includes sales/analytics endpoints"
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Product analysis failed: {str(e)}",
            "tool": "get_product_sales_velocity"
        }
