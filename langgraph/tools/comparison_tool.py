"""
Period Comparison Tool for LangGraph
Compares metrics between different time periods
"""

from langchain_core.tools import tool
import requests
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import random

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
X_TENANT_ID = os.getenv("X_TENANT_ID", "11111111-1111-1111-1111-111111111111")

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
        current_period: Current analysis period (this_week, this_month, this_quarter)
        comparison_period: Period to compare against (last_week, last_month, last_quarter)
        metric: Metric to compare (revenue, sales_volume, profit_margin)
        product_id: Specific product comparison
        category: Product category comparison
    
    Returns:
        Comparison data with percentage changes and insights
    """
    
    try:
        # Mock comparison data - in production would query historical sales data
        period_mapping = {
            "this_week": {"label": "This Week", "days": 7},
            "this_month": {"label": "This Month", "days": 30},
            "this_quarter": {"label": "This Quarter", "days": 90},
            "last_week": {"label": "Last Week", "days": 7},
            "last_month": {"label": "Last Month", "days": 30},
            "last_quarter": {"label": "Last Quarter", "days": 90}
        }
        
        current_info = period_mapping.get(current_period, {"label": current_period, "days": 30})
        comparison_info = period_mapping.get(comparison_period, {"label": comparison_period, "days": 30})
        
        # Generate mock comparison data
        if metric == "revenue":
            current_value = random.uniform(75000, 95000)
            comparison_value = random.uniform(65000, 85000)
            unit = "₹"
        elif metric == "sales_volume":
            current_value = random.uniform(800, 1200)
            comparison_value = random.uniform(700, 1100)
            unit = "units"
        elif metric == "profit_margin":
            current_value = random.uniform(20, 35)
            comparison_value = random.uniform(18, 32)
            unit = "%"
        else:
            current_value = random.uniform(100, 200)
            comparison_value = random.uniform(90, 180)
            unit = ""
            
        # Calculate changes
        percentage_change = ((current_value - comparison_value) / comparison_value) * 100
        absolute_change = current_value - comparison_value
        
        # Determine trend
        if percentage_change > 10:
            trend = "Strong Growth"
            trend_emoji = "📈"
        elif percentage_change > 0:
            trend = "Moderate Growth"
            trend_emoji = "↗️"
        elif percentage_change > -10:
            trend = "Slight Decline"
            trend_emoji = "↘️"
        else:
            trend = "Significant Decline"
            trend_emoji = "📉"
            
        # Generate insights based on the data
        insights = []
        
        if percentage_change > 0:
            insights.append(f"Positive momentum with {percentage_change:.1f}% improvement")
            if metric == "revenue":
                insights.append("Consider scaling successful strategies")
        else:
            insights.append(f"Performance declined by {abs(percentage_change):.1f}%")
            insights.append("Investigate factors causing the decline")
            
        # Add product-specific insights
        if product_id or category:
            if percentage_change > 15:
                insights.append("This product/category shows exceptional growth")
            elif percentage_change < -15:
                insights.append("This product/category needs immediate attention")
                
        return {
            "success": True,
            "comparison": {
                "current_period": {
                    "name": current_info["label"],
                    "value": round(current_value, 2),
                    "metric": metric,
                    "unit": unit
                },
                "comparison_period": {
                    "name": comparison_info["label"],
                    "value": round(comparison_value, 2),
                    "metric": metric,
                    "unit": unit
                }
            },
            "changes": {
                "percentage_change": round(percentage_change, 1),
                "absolute_change": round(absolute_change, 2),
                "trend": trend,
                "trend_emoji": trend_emoji,
                "direction": "up" if percentage_change > 0 else "down"
            },
            "insights": insights,
            "recommendations": [
                "Monitor trends weekly for early detection of changes",
                "Compare against industry benchmarks when available",
                "Set up alerts for significant performance shifts"
            ],
            "generated_at": datetime.now().isoformat()
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
    metric: str = "revenue"
) -> Dict[str, Any]:
    """
    Analyze what's driving growth or decline in specified metrics.
    
    Args:
        time_period: Period to analyze
        metric: Metric to analyze drivers for
        
    Returns:
        Analysis of growth drivers and contributing factors
    """
    
    try:
        # Get inventory data to simulate growth analysis
        inventory_data = make_api_call("/api/v1/inventory")
        
        if inventory_data.get("error"):
            return inventory_data
            
        inventory_items = inventory_data.get("inventory_items", [])
        
        # Analyze contributing factors
        growth_drivers = []
        decline_factors = []
        
        for item in inventory_items:
            if item.get("type") == "menu_item":
                has_activity = item.get("has_recent_activity", False)
                stock_status = item.get("stock_status")
                
                # Mock growth contribution analysis
                if has_activity and "Kerala" in item.get("name", ""):
                    contribution = random.uniform(8000, 15000)
                    growth_drivers.append({
                        "product_name": item.get("name"),
                        "contribution": round(contribution, 2),
                        "factor": "Strong regional appeal and quality",
                        "growth_rate": f"+{random.uniform(10, 25):.1f}%"
                    })
                elif stock_status in ["out_of_stock", "low_stock"]:
                    lost_revenue = random.uniform(2000, 8000)
                    decline_factors.append({
                        "product_name": item.get("name"),
                        "impact": round(lost_revenue, 2),
                        "factor": f"Stock issues - {stock_status}",
                        "decline_rate": f"-{random.uniform(5, 20):.1f}%"
                    })
                    
        # Sort by impact
        growth_drivers.sort(key=lambda x: x["contribution"], reverse=True)
        decline_factors.sort(key=lambda x: x["impact"], reverse=True)
        
        return {
            "success": True,
            "analysis_period": time_period,
            "metric_analyzed": metric,
            "growth_drivers": growth_drivers[:5],  # Top 5
            "decline_factors": decline_factors[:3],  # Top 3
            "net_impact": {
                "total_growth_contribution": sum(d["contribution"] for d in growth_drivers),
                "total_decline_impact": sum(d["impact"] for d in decline_factors)
            },
            "key_insights": [
                "Kerala-style items consistently drive growth",
                "Stock management directly impacts sales performance",
                "Weekend patterns show 25% higher performance"
            ],
            "recommendations": [
                "Invest more in Kerala-style menu development",
                "Improve inventory planning to reduce stockouts",
                "Optimize weekend staffing and inventory"
            ]
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Growth driver analysis failed: {str(e)}",
            "tool": "analyze_growth_drivers"
        }
