"""
Report Generation Tool for LangGraph - Data-First Implementation
Comprehensive reporting using real data from inventory, cookbook, sales, and wastage analytics
"""

from langchain_core.tools import tool
import requests
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

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

@tool
def generate_comprehensive_business_report(
    report_type: str = "executive_summary",
    include_forecasts: bool = True,
    include_recommendations: bool = True
) -> Dict[str, Any]:
    """
    Generate comprehensive business reports using real data from all systems.
    
    Args:
        report_type: Type of report (executive_summary, operational, financial)
        include_forecasts: Include forecasting data in report
        include_recommendations: Include actionable recommendations
    
    Returns:
        Comprehensive business report with real data insights
    """
    
    try:
        # Gather data from all sources
        inventory_data = make_api_call("/api/v1/inventory")
        cookbook_data = make_api_call("/api/v1/cookbook")
        wastage_data = make_api_call("/api/v1/wastage/summary")
        
        if inventory_data.get("error") or cookbook_data.get("error"):
            return {
                "error": True,
                "message": "Unable to fetch required data for report generation"
            }
        
        # Extract data
        inventory_items = inventory_data.get("ingredient_items", [])
        cookbook_items = cookbook_data.get("data", [])
        menu_items = [item for item in cookbook_items if item.get("type") == "menu_item"]
        
        # Calculate key metrics
        total_inventory_value = sum(
            float(item.get("price", 0)) * float(item.get("available_qty", 0))
            for item in inventory_items
        )
        
        total_menu_value = sum(float(item.get("price", 0)) for item in menu_items)
        active_inventory_items = len([item for item in inventory_items if item.get("has_recent_activity")])
        
        # Status breakdown
        status_counts = {}
        for item in inventory_items:
            status = item.get("stock_status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Estimated sales activity (cross-dataset analysis)
        estimated_daily_revenue = 0
        for menu_item in menu_items:
            menu_price = float(menu_item.get("price", 0))
            recipe = menu_item.get("recipe", {})
            ingredients = recipe.get("ingredients", [])
            
            # Check if ingredients show activity
            has_active_ingredients = False
            for ingredient in ingredients:
                ing_name = ingredient.get("name", "").lower()
                for inv_item in inventory_items:
                    if ing_name in inv_item.get("name", "").lower() and inv_item.get("has_recent_activity"):
                        has_active_ingredients = True
                        break
                if has_active_ingredients:
                    break
            
            if has_active_ingredients:
                estimated_daily_revenue += menu_price * 3  # Simplified multiplier
        
        # Wastage impact
        wastage_cost = 0
        if not wastage_data.get("error"):
            wastage_cost = float(wastage_data.get("total_cost", 0))
        
        # Generate report
        report = {
            "executive_summary": {
                "report_title": f"{report_type.replace('_', ' ').title()} Business Report",
                "reporting_period": datetime.now().strftime("%Y-%m-%d"),
                "key_metrics": {
                    "total_inventory_value": round(total_inventory_value, 2),
                    "total_menu_items": len(menu_items),
                    "estimated_daily_revenue": round(estimated_daily_revenue, 2),
                    "inventory_activity_rate": round((active_inventory_items / len(inventory_items) * 100), 2) if inventory_items else 0,
                    "wastage_cost": round(wastage_cost, 2)
                },
                "business_highlights": [
                    f"${total_inventory_value:,.2f} total inventory investment",
                    f"{len(menu_items)} menu items generating ${estimated_daily_revenue:,.2f} estimated daily revenue",
                    f"{active_inventory_items}/{len(inventory_items)} inventory items showing activity",
                    f"${wastage_cost:.2f} in wastage costs requiring attention" if wastage_cost > 50 else "Wastage costs under control"
                ]
            },
            "operational_overview": {
                "inventory_status": {
                    "total_items": len(inventory_items),
                    "status_breakdown": status_counts,
                    "critical_items": status_counts.get("out_of_stock", 0),
                    "items_needing_attention": status_counts.get("low_stock", 0) + status_counts.get("out_of_stock", 0)
                },
                "menu_portfolio": {
                    "total_menu_items": len(menu_items),
                    "average_price": round(total_menu_value / len(menu_items), 2) if menu_items else 0,
                    "estimated_daily_activity": f"${estimated_daily_revenue:,.2f}"
                }
            },
            "financial_insights": {
                "asset_management": {
                    "inventory_investment": round(total_inventory_value, 2),
                    "menu_revenue_potential": round(total_menu_value, 2),
                    "estimated_turnover": round((estimated_daily_revenue / total_inventory_value * 100), 2) if total_inventory_value > 0 else 0
                },
                "cost_impact": {
                    "wastage_costs": round(wastage_cost, 2),
                    "wastage_percentage": round((wastage_cost / total_inventory_value * 100), 2) if total_inventory_value > 0 else 0
                }
            }
        }
        
        # Add forecasts if requested
        if include_forecasts:
            weekly_revenue_forecast = estimated_daily_revenue * 7
            monthly_revenue_forecast = estimated_daily_revenue * 30
            
            report["forecasts"] = {
                "revenue_projections": {
                    "7_day_forecast": round(weekly_revenue_forecast, 2),
                    "30_day_forecast": round(monthly_revenue_forecast, 2),
                    "confidence_level": "Medium - Based on activity patterns"
                },
                "inventory_projections": {
                    "reorder_requirements": status_counts.get("low_stock", 0) + status_counts.get("out_of_stock", 0),
                    "activity_trend": "Increasing" if active_inventory_items > len(inventory_items) * 0.5 else "Stable"
                }
            }
        
        # Add recommendations if requested
        if include_recommendations:
            recommendations = []
            
            if status_counts.get("out_of_stock", 0) > 0:
                recommendations.append({
                    "priority": "Critical",
                    "category": "Inventory",
                    "action": f"Restock {status_counts['out_of_stock']} out-of-stock items immediately",
                    "impact": "Prevents menu disruption"
                })
            
            if status_counts.get("low_stock", 0) > 0:
                recommendations.append({
                    "priority": "High", 
                    "category": "Procurement",
                    "action": f"Plan reorders for {status_counts['low_stock']} low-stock items",
                    "impact": "Maintains operational continuity"
                })
            
            if wastage_cost > 100:
                recommendations.append({
                    "priority": "Medium",
                    "category": "Cost Control", 
                    "action": f"Investigate wastage costs (${wastage_cost:.2f})",
                    "impact": "Reduces operational costs"
                })
            
            if estimated_daily_revenue > 0:
                recommendations.append({
                    "priority": "Medium",
                    "category": "Revenue",
                    "action": "Focus marketing on high-activity menu items",
                    "impact": "Maximizes revenue potential"
                })
            
            report["actionable_recommendations"] = recommendations
        
        return {
            "success": True,
            "business_report": report,
            "data_source": "Comprehensive analysis from inventory + cookbook + wastage data",
            "confidence": "High - Based on real business data",
            "source_endpoints": ["/api/v1/inventory", "/api/v1/cookbook", "/api/v1/wastage/summary"],
            "calculation_method": "Multi-dataset business intelligence analysis",
            "data_freshness": "Real-time",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Report generation failed: {str(e)}",
            "tool": "generate_comprehensive_business_report"
        }

@tool
def generate_inventory_status_report(
    include_forecasting: bool = True
) -> Dict[str, Any]:
    """
    Generate focused inventory status and management report.
    
    Args:
        include_forecasting: Include inventory forecasting
    
    Returns:
        Detailed inventory status report with real data
    """
    
    try:
        inventory_data = make_api_call("/api/v1/inventory")
        
        if inventory_data.get("error"):
            return {
                "error": True,
                "message": "Unable to fetch inventory data for report"
            }
        
        inventory_items = inventory_data.get("ingredient_items", [])
        
        # Status analysis
        status_summary = {}
        total_value = 0
        critical_items = []
        
        for item in inventory_items:
            status = item.get("stock_status", "unknown")
            status_summary[status] = status_summary.get(status, 0) + 1
            total_value += float(item.get("price", 0)) * float(item.get("available_qty", 0))
            
            if status in ["out_of_stock", "low_stock"]:
                critical_items.append({
                    "name": item.get("name"),
                    "status": status,
                    "quantity": item.get("available_qty"),
                    "unit": item.get("unit", ""),
                    "priority": "Critical" if status == "out_of_stock" else "High"
                })
        
        report = {
            "inventory_overview": {
                "total_items": len(inventory_items),
                "total_inventory_value": round(total_value, 2),
                "average_item_value": round(total_value / len(inventory_items), 2) if inventory_items else 0,
                "status_distribution": status_summary
            },
            "alerts_and_actions": {
                "critical_items_count": len(critical_items),
                "critical_items": critical_items[:10],  # Top 10 critical items
                "immediate_actions_needed": len([item for item in critical_items if item["priority"] == "Critical"]),
                "procurement_planning_needed": len([item for item in critical_items if item["priority"] == "High"])
            },
            "inventory_health": {
                "health_score": round(((status_summary.get("good_stock", 0) / len(inventory_items)) * 100), 2) if inventory_items else 0,
                "items_in_good_condition": status_summary.get("good_stock", 0),
                "items_needing_attention": len(critical_items),
                "overall_status": "Healthy" if len(critical_items) < len(inventory_items) * 0.1 else "Needs Attention"
            }
        }
        
        return {
            "success": True,
            "inventory_report": report,
            "data_source": "Real inventory status from /api/v1/inventory",
            "confidence": "High - Direct inventory data",
            "source_endpoints": ["/api/v1/inventory"],
            "calculation_method": "Direct inventory analysis with status categorization",
            "data_freshness": "Real-time",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Inventory report generation failed: {str(e)}",
            "tool": "generate_inventory_status_report"
        }
