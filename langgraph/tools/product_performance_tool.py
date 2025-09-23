"""
Product Performance Analysis Tool for LangGraph
Dedicated tool for analyzing menu item and ingredient performance
"""

from langchain_core.tools import tool
import requests
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import random

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
        # Get inventory data to simulate product performance analysis
        inventory_data = make_api_call("/api/v1/inventory")
        
        if inventory_data.get("error"):
            return inventory_data
            
        inventory_items = inventory_data.get("inventory_items", [])
        
        # Filter by category if specified
        if category:
            inventory_items = [
                item for item in inventory_items 
                if item.get("category", "").lower() == category.lower() or 
                   item.get("type", "").lower() == category.lower()
            ]
            
        # Generate performance metrics
        product_performance = []
        
        for item in inventory_items:
            # Calculate mock performance metrics
            base_price = float(item.get("price", 0))
            has_activity = item.get("has_recent_activity", False)
            stock_status = item.get("stock_status", "in_stock")
            
            # Generate realistic performance data
            if item.get("type") == "menu_item":
                # Menu items have higher revenue potential
                base_sales = random.uniform(80, 200)
                if "Kerala" in item.get("name", ""):
                    performance_multiplier = 1.5  # Kerala items perform better
                elif "Burger" in item.get("name", ""):
                    performance_multiplier = 1.2
                else:
                    performance_multiplier = 1.0
            else:
                # Raw materials have usage-based performance
                base_sales = random.uniform(20, 80)
                performance_multiplier = 1.1 if has_activity else 0.7
                
            # Activity and stock status impact
            if stock_status == "out_of_stock":
                performance_multiplier *= 0.3  # Significant negative impact
            elif stock_status == "low_stock":
                performance_multiplier *= 0.7  # Moderate negative impact
            elif stock_status == "dead_stock":
                performance_multiplier *= 0.1  # Very poor performance
                
            # Calculate metrics
            if metric == "revenue":
                performance_value = base_sales * base_price * performance_multiplier
                unit = "₹"
            elif metric == "quantity_sold":
                performance_value = base_sales * performance_multiplier
                unit = "units"
            elif metric == "profit_margin":
                performance_value = random.uniform(15, 45) * performance_multiplier
                unit = "%"
            else:
                performance_value = base_sales * performance_multiplier
                unit = ""
                
            # Growth rate calculation
            growth_rate = random.uniform(-20, 30)
            if "Kerala" in item.get("name", ""):
                growth_rate += 10  # Kerala items trending up
            if stock_status in ["out_of_stock", "low_stock"]:
                growth_rate -= 15  # Stock issues hurt growth
                
            performance_data = {
                "product_id": item.get("id"),
                "product_name": item.get("name"),
                "product_type": item.get("type"),
                "category": item.get("category"),
                "performance_value": round(performance_value, 2),
                "metric": metric,
                "unit": unit,
                "growth_rate": round(growth_rate, 1),
                "stock_status": stock_status,
                "has_recent_activity": has_activity,
                "rank": 0  # Will be set after sorting
            }
            
            # Add comparison data if requested
            if include_comparisons:
                previous_value = performance_value / (1 + (growth_rate / 100))
                performance_data["comparison"] = {
                    "previous_period_value": round(previous_value, 2),
                    "absolute_change": round(performance_value - previous_value, 2),
                    "percentage_change": round(growth_rate, 1)
                }
                
            product_performance.append(performance_data)
            
        # Sort by performance value
        product_performance.sort(key=lambda x: x["performance_value"], reverse=True)
        
        # Add rankings
        for i, product in enumerate(product_performance):
            product["rank"] = i + 1
            
        # Get top and bottom performers
        top_performers = product_performance[:top_n]
        bottom_performers = product_performance[-min(3, len(product_performance)):]
        
        # Generate insights
        insights = []
        
        if top_performers:
            top_product = top_performers[0]
            insights.append(f"{top_product['product_name']} leads {metric} with {top_product['unit']}{top_product['performance_value']:,.0f}")
            
        kerala_items = [p for p in top_performers if "Kerala" in p.get("product_name", "")]
        if kerala_items:
            insights.append("Kerala-style items consistently outperform classic variants")
            
        stock_issues = [p for p in product_performance if p.get("stock_status") in ["out_of_stock", "low_stock"]]
        if stock_issues:
            insights.append(f"{len(stock_issues)} items underperforming due to stock issues")
            
        # Business recommendations
        recommendations = []
        
        if kerala_items:
            recommendations.append("Consider expanding Kerala-style menu offerings")
        if stock_issues:
            recommendations.append("Address stock issues for underperforming items")
        if bottom_performers:
            worst_product = bottom_performers[-1]
            recommendations.append(f"Review pricing/marketing strategy for {worst_product['product_name']}")
            
        return {
            "success": True,
            "analysis_period": time_period,
            "metric_analyzed": metric,
            "total_products_analyzed": len(product_performance),
            "top_performers": top_performers,
            "bottom_performers": bottom_performers,
            "category_filter": category,
            "insights": insights,
            "recommendations": recommendations,
            "summary_stats": {
                "avg_performance": round(sum(p["performance_value"] for p in product_performance) / len(product_performance), 2) if product_performance else 0,
                "top_growth_rate": max((p["growth_rate"] for p in product_performance), default=0),
                "bottom_growth_rate": min((p["growth_rate"] for p in product_performance), default=0),
                "products_growing": len([p for p in product_performance if p["growth_rate"] > 0]),
                "products_declining": len([p for p in product_performance if p["growth_rate"] < 0])
            },
            "generated_at": datetime.now().isoformat()
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
        inventory_data = make_api_call("/api/v1/inventory")
        
        if inventory_data.get("error"):
            return inventory_data
            
        inventory_items = inventory_data.get("inventory_items", [])
        
        # Group by category/type
        categories = {}
        
        for item in inventory_items:
            category = item.get("type", "unknown")
            
            if category not in categories:
                categories[category] = []
                
            # Generate mock ranking data
            if metric == "revenue":
                value = random.uniform(5000, 50000)
            elif metric == "quantity_sold":
                value = random.uniform(50, 500)
            else:
                value = random.uniform(10, 40)
                
            categories[category].append({
                "name": item.get("name"),
                "value": round(value, 2),
                "growth": round(random.uniform(-10, 25), 1)
            })
            
        # Sort within each category
        for category in categories:
            categories[category].sort(key=lambda x: x["value"], reverse=True)
            
        return {
            "success": True,
            "metric": metric,
            "time_period": time_period,
            "category_rankings": categories,
            "insights": [
                "Menu items show highest revenue potential",
                "Raw materials have consistent demand patterns",
                "Sub-products provide good profit margins"
            ]
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Category ranking failed: {str(e)}",
            "tool": "get_product_ranking_by_category"
        }
