"""
Report Generation Tool for LangGraph
Creates structured reports and summaries for sales analytics
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
def generate_sales_report(
    report_type: str = "weekly",
    time_period: str = "last_week",
    include_forecasts: bool = True,
    include_inventory: bool = True,
    format_type: str = "summary"
) -> Dict[str, Any]:
    """
    Generate comprehensive sales reports with analytics and insights.
    
    Args:
        report_type: Type of report (daily, weekly, monthly, quarterly)
        time_period: Period to analyze (last_week, last_month, etc.)
        include_forecasts: Include sales predictions in the report
        include_inventory: Include inventory analysis
        format_type: Format (summary, detailed, executive)
        
    Returns:
        Structured report with sales data, trends, and recommendations
    """
    
    try:
        # Generate mock comprehensive report
        # In production, this would aggregate data from multiple tools
        
        # Mock sales data
        total_revenue = random.uniform(70000, 120000)
        total_orders = random.randint(800, 1500)
        avg_order_value = total_revenue / total_orders
        
        # Mock product performance
        top_products = [
            {"name": "Kerala Burger", "revenue": 32000, "growth": 15.2},
            {"name": "Chicken Burger", "revenue": 28000, "growth": 8.5},
            {"name": "Fish Burger", "revenue": 18000, "growth": 5.1}
        ]
        
        # Mock trends
        trends = {
            "revenue_growth": random.uniform(5, 20),
            "order_growth": random.uniform(3, 15),
            "customer_satisfaction": random.uniform(4.0, 4.8),
            "peak_hours": ["12:00-14:00", "19:00-21:00"],
            "peak_days": ["Friday", "Saturday", "Sunday"]
        }
        
        # Report sections
        report = {
            "report_metadata": {
                "type": report_type,
                "period": time_period,
                "generated_at": datetime.now().isoformat(),
                "format": format_type,
                "data_sources": ["sales", "inventory", "forecasts"] if include_forecasts else ["sales", "inventory"]
            },
            
            "executive_summary": {
                "total_revenue": round(total_revenue, 2),
                "total_orders": total_orders,
                "avg_order_value": round(avg_order_value, 2),
                "revenue_growth": round(trends["revenue_growth"], 1),
                "key_insights": [
                    f"Revenue grew {trends['revenue_growth']:.1f}% compared to previous period",
                    f"Kerala Burger drives {(32000/total_revenue)*100:.1f}% of total revenue",
                    "Weekend performance 25% higher than weekdays"
                ]
            },
            
            "sales_performance": {
                "total_revenue": round(total_revenue, 2),
                "revenue_breakdown": {
                    "menu_items": round(total_revenue * 0.75, 2),
                    "combos": round(total_revenue * 0.25, 2)
                },
                "top_performers": top_products,
                "growth_trends": trends,
                "peak_performance": {
                    "hours": trends["peak_hours"],
                    "days": trends["peak_days"]
                }
            }
        }
        
        # Add forecasts if requested
        if include_forecasts:
            report["forecasts"] = {
                "next_period_revenue": {
                    "predicted": round(total_revenue * 1.15, 2),
                    "confidence": "85%",
                    "growth_expected": "+15%"
                },
                "top_product_forecasts": [
                    {"name": "Kerala Burger", "predicted_revenue": 38000},
                    {"name": "Chicken Burger", "predicted_revenue": 32000}
                ],
                "inventory_implications": [
                    "Need 200 burger buns for forecasted demand",
                    "Increase ground beef order by 25kg"
                ]
            }
            
        # Add inventory section if requested
        if include_inventory:
            report["inventory_status"] = {
                "total_items": 22,
                "status_breakdown": {
                    "in_stock": 12,
                    "low_stock": 4,
                    "out_of_stock": 2,
                    "expiring_soon": 2,
                    "dead_stock": 2
                },
                "critical_actions": [
                    "Reorder burger buns (low stock)",
                    "Use expiring tomatoes in promotions",
                    "Address bacon stockout affecting menu"
                ],
                "inventory_value": round(random.uniform(50000, 80000), 2)
            }
            
        # Add recommendations
        report["recommendations"] = {
            "immediate_actions": [
                "Focus marketing on Kerala Burger (top performer)",
                "Address stock issues for underperforming items",
                "Optimize weekend staffing for peak demand"
            ],
            "strategic_initiatives": [
                "Expand Kerala-style menu offerings",
                "Implement dynamic pricing for peak hours",
                "Develop customer loyalty program"
            ],
            "risk_mitigation": [
                "Diversify supplier base for critical ingredients",
                "Implement automated reorder points",
                "Monitor competitor pricing weekly"
            ]
        }
        
        return {
            "success": True,
            "report": report,
            "summary": f"{report_type.title()} sales report for {time_period} generated successfully",
            "key_metrics": {
                "revenue": round(total_revenue, 2),
                "growth": round(trends["revenue_growth"], 1),
                "orders": total_orders,
                "top_product": top_products[0]["name"]
            }
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Report generation failed: {str(e)}",
            "tool": "generate_sales_report"
        }

@tool
def create_performance_summary(
    focus_area: str = "overall",
    time_period: str = "last_month"
) -> Dict[str, Any]:
    """
    Create a focused performance summary for specific business areas.
    
    Args:
        focus_area: Area to focus on (overall, menu_items, raw_materials, forecasting)
        time_period: Period for analysis
        
    Returns:
        Targeted performance summary with actionable insights
    """
    
    try:
        summaries = {
            "overall": {
                "title": "Overall Business Performance",
                "metrics": {
                    "revenue": f"₹{random.uniform(80000, 120000):,.0f}",
                    "growth": f"+{random.uniform(8, 18):.1f}%",
                    "efficiency": "87%",
                    "customer_satisfaction": "4.3/5"
                },
                "highlights": [
                    "Strong revenue growth driven by Kerala-style items",
                    "Weekend performance exceeds weekday by 25%",
                    "Inventory turnover improved significantly"
                ],
                "concerns": [
                    "Stock-outs affecting 2 menu items",
                    "Raw material costs increased 8%"
                ]
            },
            
            "menu_items": {
                "title": "Menu Item Performance Analysis", 
                "top_performers": [
                    "Kerala Burger: ₹32k (+15%)",
                    "Chicken Burger: ₹28k (+8%)",
                    "Fish Burger: ₹18k (+5%)"
                ],
                "underperformers": [
                    "Seafood Combo: ₹3k (-5%)",
                    "Classic Combo: ₹5k (+2%)"
                ],
                "insights": [
                    "Regional flavors outperform classic items",
                    "Burger formats more popular than combos",
                    "Price elasticity suggests room for premium pricing"
                ]
            },
            
            "raw_materials": {
                "title": "Raw Material Usage & Efficiency",
                "high_velocity": [
                    "Ground Beef: High demand, low stock",
                    "Burger Buns: Consistent usage, reorder needed",
                    "Vegetables: Seasonal fluctuations"
                ],
                "cost_trends": [
                    "Protein costs stable",
                    "Vegetable prices increased 12%",
                    "Packaging costs decreased 3%"
                ],
                "optimization": [
                    "Bulk purchasing for ground beef recommended",
                    "Local sourcing for vegetables could reduce costs",
                    "Consider alternative protein options"
                ]
            }
        }
        
        selected_summary = summaries.get(focus_area, summaries["overall"])
        
        return {
            "success": True,
            "focus_area": focus_area,
            "time_period": time_period,
            "summary": selected_summary,
            "action_items": [
                "Review underperforming items for potential menu changes",
                "Optimize inventory levels based on sales velocity",
                "Plan promotional campaigns for slow-moving items"
            ],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Performance summary creation failed: {str(e)}",
            "tool": "create_performance_summary"
        }
