"""
Inventory Status Tool for LangGraph
Handles inventory queries with sales context
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
def get_inventory_status(
    filter_status: Optional[str] = None,
    product_id: Optional[str] = None,
    include_batches: bool = False,
    include_sales_context: bool = True
) -> Dict[str, Any]:
    """
    Get current inventory levels and stock status information with sales context.
    
    Args:
        filter_status: Filter by status (low_stock, out_of_stock, expiring_soon, dead_stock)
        product_id: Specific product inventory
        include_batches: Include batch and expiry details
        include_sales_context: Include sales velocity and recommendations
    
    Returns:
        Current inventory data with stock status and sales-driven recommendations
    """
    
    try:
        # Get inventory data
        if product_id:
            inventory_data = make_api_call(f"/api/v1/inventory/{product_id}")
        else:
            inventory_data = make_api_call("/api/v1/inventory")
            
        if inventory_data.get("error"):
            return inventory_data
            
        # Extract inventory items
        if product_id:
            inventory_items = inventory_data.get("data", [])
        else:
            inventory_items = inventory_data.get("inventory_items", [])
            
        # Apply status filter if specified
        if filter_status:
            inventory_items = [
                item for item in inventory_items 
                if item.get("stock_status") == filter_status
            ]
            
        # Enhance with sales context
        enhanced_items = []
        for item in inventory_items:
            enhanced_item = {
                "id": item.get("id"),
                "name": item.get("name"),
                "type": item.get("type"),
                "available_qty": item.get("available_qty"),
                "unit": item.get("unit"),
                "price": item.get("price"),
                "stock_status": item.get("stock_status"),
                "last_updated": item.get("last_updated"),
                "has_recent_activity": item.get("has_recent_activity")
            }
            
            # Add sales context if requested
            if include_sales_context:
                # Mock sales velocity based on activity and type
                if item.get("has_recent_activity") and item.get("type") == "menu_item":
                    sales_velocity = "High"
                    recommendation = "Monitor closely - high turnover item"
                elif item.get("stock_status") == "low_stock":
                    sales_velocity = "Medium"
                    recommendation = "Reorder soon to avoid stockout"
                elif item.get("stock_status") == "dead_stock":
                    sales_velocity = "Low" 
                    recommendation = "Consider promotional pricing or menu changes"
                else:
                    sales_velocity = "Medium"
                    recommendation = "Stock levels healthy"
                    
                enhanced_item["sales_context"] = {
                    "sales_velocity": sales_velocity,
                    "recommendation": recommendation,
                    "reorder_priority": "High" if item.get("stock_status") in ["low_stock", "out_of_stock"] else "Low"
                }
                
            # Add batch information if requested
            if include_batches and item.get("batches"):
                enhanced_item["batches"] = item.get("batches")
                enhanced_item["earliest_expiry"] = item.get("earliest_expiry_date")
                
            enhanced_items.append(enhanced_item)
            
        # Create summary
        summary = inventory_data.get("summary", {})
        if include_sales_context:
            summary["sales_insights"] = {
                "high_velocity_items": len([i for i in enhanced_items if i.get("sales_context", {}).get("sales_velocity") == "High"]),
                "reorder_priorities": len([i for i in enhanced_items if i.get("sales_context", {}).get("reorder_priority") == "High"]),
                "dead_stock_value": sum(float(i.get("price", 0)) * float(i.get("available_qty", 0)) for i in enhanced_items if i.get("stock_status") == "dead_stock")
            }
            
        return {
            "success": True,
            "inventory_items": enhanced_items,
            "summary": summary,
            "filter_applied": filter_status,
            "total_items": len(enhanced_items),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Inventory status query failed: {str(e)}",
            "tool": "get_inventory_status"
        }

@tool
def check_stock_alerts(
    alert_types: List[str] = ["low_stock", "expiring_soon", "dead_stock"]
) -> Dict[str, Any]:
    """
    Check for inventory alerts that need immediate attention.
    
    Args:
        alert_types: Types of alerts to check for
        
    Returns:
        Critical inventory alerts with sales impact analysis
    """
    
    try:
        inventory_data = make_api_call("/api/v1/inventory")
        
        if inventory_data.get("error"):
            return inventory_data
            
        inventory_items = inventory_data.get("inventory_items", [])
        
        alerts = []
        
        for item in inventory_items:
            stock_status = item.get("stock_status")
            
            if stock_status in alert_types:
                alert = {
                    "product_name": item.get("name"),
                    "alert_type": stock_status,
                    "current_qty": item.get("available_qty"),
                    "unit": item.get("unit"),
                    "severity": "Critical" if stock_status == "out_of_stock" else "High" if stock_status == "low_stock" else "Medium"
                }
                
                # Add sales impact
                if item.get("type") == "menu_item" and item.get("has_recent_activity"):
                    alert["sales_impact"] = "High - affects menu availability"
                elif stock_status == "expiring_soon":
                    alert["sales_impact"] = "Medium - consider promotions"
                    alert["expiry_date"] = item.get("earliest_expiry_date")
                else:
                    alert["sales_impact"] = "Low"
                    
                alerts.append(alert)
                
        # Sort by severity
        severity_order = {"Critical": 3, "High": 2, "Medium": 1}
        alerts.sort(key=lambda x: severity_order.get(x["severity"], 0), reverse=True)
        
        return {
            "success": True,
            "alerts": alerts,
            "total_alerts": len(alerts),
            "critical_count": len([a for a in alerts if a["severity"] == "Critical"]),
            "recommendations": [
                "Address critical alerts immediately to prevent sales disruption",
                "Plan promotional strategies for expiring items",
                "Review dead stock for potential write-offs"
            ]
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Stock alerts check failed: {str(e)}",
            "tool": "check_stock_alerts"
        }
