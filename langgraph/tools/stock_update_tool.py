"""
Stock Query Tool for LangGraph
Handles read-only inventory queries for analysis purposes
"""

from langchain_core.tools import tool
import requests
import os
from typing import Optional, Dict, Any
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
        else:
            raise ValueError(f"Only GET requests allowed for analysis - attempted: {method}")
            
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": True,
            "message": f"API call failed: {str(e)}",
            "endpoint": endpoint
        }

@tool
def get_product_details(
    product_id: str
) -> Dict[str, Any]:
    """
    Get detailed information for a specific product (read-only analysis).
    
    Args:
        product_id: Product ID to get details for
        
    Returns:
        Detailed product information from inventory
    """
    
    try:
        # Get specific product inventory data
        inventory_data = make_api_call(f"/api/v1/inventory/{product_id}")
        
        if inventory_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to connect to backend server: {inventory_data.get('message')}",
                "endpoint": f"/api/v1/inventory/{product_id}",
                "suggestion": "Please ensure the inventory backend API is running on port 8000"
            }
            
        # Backend returns: {"data": [{"item_data_here"}]} or {"data": []} for individual items
        data_wrapper = inventory_data.get("data", [])
        if not data_wrapper or len(data_wrapper) == 0:
            return {
                "error": True,
                "message": f"Product {product_id} not found in inventory",
                "endpoint": f"/api/v1/inventory/{product_id}"
            }
            
        item = data_wrapper[0]
        
        return {
            "success": True,
            "product_details": {
                "id": item.get("id"),
                "name": item.get("name"),
                "type": item.get("type"),
                "category": item.get("category"),
                "available_qty": item.get("available_qty"),
                "unit": item.get("unit"),
                "price": item.get("price"),
                "stock_status": item.get("stock_status"),
                "last_updated": item.get("last_updated"),
                "has_recent_activity": item.get("has_recent_activity"),
                "batches": item.get("batches", []),
                "earliest_expiry_date": item.get("earliest_expiry_date")
            },
            "analysis_context": {
                "stock_health": "Good" if item.get("stock_status") == "in_stock" else "Needs attention",
                "activity_level": "Active" if item.get("has_recent_activity") else "Inactive",
                "expiry_concern": "Yes" if item.get("earliest_expiry_date") else "No"
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Product details query failed: {str(e)}",
            "tool": "get_product_details"
        }