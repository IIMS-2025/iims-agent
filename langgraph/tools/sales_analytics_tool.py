"""
Sales Analytics Tool for LangGraph - Data-First Implementation
Cross-dataset analysis using inventory + cookbook + wastage data to derive sales insights
"""

from langchain_core.tools import tool
import requests
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
X_TENANT_ID = os.getenv("X_TENANT_ID", "11111111-1111-1111-1111-111111111111")
X_LOCATION_ID = os.getenv("X_LOCATION_ID", "22222222-2222-2222-2222-222222222222")

def make_api_call(endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
    """Helper function to make API calls with proper headers"""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "X-Tenant-ID": X_TENANT_ID,
        "Content-Type": "application/json"
    }
    
    # Add location header for wastage endpoints
    if "/wastage" in endpoint:
        headers["X-Location-ID"] = X_LOCATION_ID
    
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

def discover_sales_endpoints() -> List[str]:
    """
    Discover if any undocumented sales endpoints exist
    """
    potential_sales_endpoints = [
        "/api/v1/sales",
        "/api/v1/sales/total-sales", 
        "/api/v1/sales-analytics",
        "/api/v1/orders",
        "/api/v1/transactions"
    ]
    
    available_endpoints = []
    for endpoint in potential_sales_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", 
                                  headers={"X-Tenant-ID": X_TENANT_ID}, 
                                  timeout=3)
            if response.status_code != 404:
                available_endpoints.append(endpoint)
        except:
            pass
    
    return available_endpoints

@tool
def get_total_sales(
    date_range: str = "today",
    include_forecasting: bool = False
) -> Dict[str, Any]:
    """
    Calculate sales from real inventory movements and cookbook pricing.
    
    Args:
        date_range: Time period (today, last_7_days, last_30_days)
        include_forecasting: Include sales forecasting based on trends
    
    Returns:
        Sales analysis calculated from inventory movements + cookbook pricing
    """
    
    try:
        # First, check if direct sales endpoints exist
        sales_endpoints = discover_sales_endpoints()
        
        if sales_endpoints:
            # Try direct sales endpoint first
            for endpoint in sales_endpoints:
                sales_data = make_api_call(endpoint)
                if not sales_data.get("error"):
                    return {
                        "success": True,
                        "sales_data": sales_data,
                        "data_source": f"Direct sales API: {endpoint}",
                        "confidence": "High - Real sales data",
                        "source_endpoints": [endpoint],
                        "data_freshness": "Real-time",
                        "generated_at": datetime.now().isoformat()
                    }
        
        # Fallback: Cross-dataset analysis
        # Fetch inventory data
        inventory_data = make_api_call("/api/v1/inventory")
        if inventory_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to fetch inventory data: {inventory_data.get('message')}",
                "endpoints_tried": ["/api/v1/inventory"]
            }
        
        # Fetch cookbook data
        cookbook_data = make_api_call("/api/v1/cookbook")
        if cookbook_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to fetch cookbook data: {cookbook_data.get('message')}",
                "endpoints_tried": ["/api/v1/cookbook"]
            }
        
        # Extract data
        inventory_items = inventory_data.get("ingredient_items", [])
        cookbook_items = cookbook_data.get("data", [])
        
        # Calculate sales indicators from inventory movements
        total_revenue_estimate = 0
        items_with_activity = 0
        high_turnover_items = []
        category_sales = {}
        
        # Create pricing lookup from cookbook
        menu_pricing = {}
        for item in cookbook_items:
            if item.get("type") == "menu_item":
                menu_pricing[item.get("name", "").lower()] = {
                    "price": float(item.get("price", 0)),
                    "category": item.get("category", "uncategorized"),
                    "id": item.get("id", "")
                }
        
        # Analyze inventory for sales indicators
        for item in inventory_items:
            if item.get("has_recent_activity"):
                items_with_activity += 1
                item_name = item.get("name", "").lower()
                
                # If this ingredient is used in menu items, estimate sales
                for menu_name, menu_info in menu_pricing.items():
                    # Simple matching (could be improved with recipe analysis)
                    if item_name in menu_name or any(word in item_name for word in menu_name.split()):
                        # Estimate sales based on activity and stock levels
                        if item.get("stock_status") == "low_stock":
                            # High usage indicates sales
                            estimated_portions = 10  # Simplified estimation
                            estimated_revenue = estimated_portions * menu_info["price"]
                            total_revenue_estimate += estimated_revenue
                            
                            # Track category
                            category = menu_info["category"]
                            if category not in category_sales:
                                category_sales[category] = {"revenue": 0, "items": 0}
                            category_sales[category]["revenue"] += estimated_revenue
                            category_sales[category]["items"] += 1
                            
                            high_turnover_items.append({
                                "name": item.get("name"),
                                "menu_item": menu_name,
                                "estimated_revenue": estimated_revenue,
                                "status": item.get("stock_status")
                            })
        
        # Calculate date range specifics
        if date_range == "today":
            period_multiplier = 1
            analysis_period = "Daily estimate"
        elif date_range == "last_7_days":
            period_multiplier = 7
            analysis_period = "7-day estimate"
        elif date_range == "last_30_days":
            period_multiplier = 30
            analysis_period = "30-day estimate"
        else:
            period_multiplier = 1
            analysis_period = "Daily estimate"
        
        # Adjust estimates for time period
        total_revenue_estimate *= period_multiplier
        
        # Calculate metrics
        avg_revenue_per_active_item = total_revenue_estimate / items_with_activity if items_with_activity > 0 else 0
        
        # Top categories by estimated revenue
        top_categories = sorted(category_sales.items(), key=lambda x: x[1]["revenue"], reverse=True)[:5]
        
        sales_analysis = {
            "period": analysis_period,
            "revenue_metrics": {
                "estimated_total_revenue": round(total_revenue_estimate, 2),
                "active_items_count": items_with_activity,
                "average_revenue_per_active_item": round(avg_revenue_per_active_item, 2),
                "high_turnover_items_count": len(high_turnover_items)
            },
            "category_performance": [
                {
                    "category": category,
                    "estimated_revenue": round(data["revenue"], 2),
                    "active_items": data["items"],
                    "percentage_of_total": round((data["revenue"] / total_revenue_estimate * 100), 2) if total_revenue_estimate > 0 else 0
                }
                for category, data in top_categories
            ],
            "high_performance_items": high_turnover_items[:10],
            "insights": []
        }
        
        # Add insights based on analysis
        if items_with_activity > len(inventory_items) * 0.3:
            sales_analysis["insights"].append("High inventory turnover indicates strong sales activity")
        
        if len(high_turnover_items) > 5:
            sales_analysis["insights"].append("Multiple high-turnover items detected - busy sales period")
        
        if top_categories and top_categories[0][1]["revenue"] > total_revenue_estimate * 0.5:
            sales_analysis["insights"].append(f"'{top_categories[0][0]}' category dominates sales")
        
        # Include forecasting if requested
        forecasting_data = {}
        if include_forecasting:
            # Simple trend forecasting based on current activity
            if items_with_activity > 0:
                growth_factor = min(items_with_activity / len(inventory_items), 0.2)  # Cap at 20% growth
                forecasting_data = {
                    "next_period_estimate": round(total_revenue_estimate * (1 + growth_factor), 2),
                    "growth_indicator": f"{growth_factor * 100:.1f}%",
                    "forecast_confidence": "Medium - Based on inventory activity patterns"
                }
        
        return {
            "success": True,
            "sales_analysis": sales_analysis,
            "forecasting": forecasting_data if include_forecasting else None,
            "data_source": "Calculated from inventory movements + cookbook pricing",
            "confidence": "Medium - Derived from real data",
            "source_endpoints": ["/api/v1/inventory", "/api/v1/cookbook"],
            "calculation_method": "Cross-dataset analysis: inventory activity → menu item sales estimation",
            "limitations": [
                "Sales estimation based on inventory turnover patterns",
                "Requires recipe-ingredient mapping for accuracy",
                "Direct sales endpoints not available"
            ],
            "data_freshness": "Real-time",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Sales analysis failed: {str(e)}",
            "tool": "get_total_sales"
        }
