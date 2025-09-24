"""
Wastage Analysis Tool for LangGraph
Comprehensive tools for analyzing wastage patterns, costs, and trends
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
        "X-Location-ID": X_LOCATION_ID,
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
def get_wastage_summary(
    days_back: int = 30,
    include_trends: bool = True,
    include_cost_analysis: bool = True
) -> Dict[str, Any]:
    """
    Get comprehensive wastage summary with trends and cost analysis.
    
    Args:
        days_back: Number of days to analyze (default 30)
        include_trends: Include trend analysis over time
        include_cost_analysis: Include detailed cost breakdowns
    
    Returns:
        Wastage summary with statistics, trends, and business insights
    """
    
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Get wastage summary from API
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
        wastage_summary = make_api_call(f"/api/v1/wastage/summary?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}")
        
        if wastage_summary.get("error"):
            return {
                "error": True,
                "message": f"Unable to connect to backend server: {wastage_summary.get('message')}",
                "endpoint": "/api/v1/wastage/summary",
                "suggestion": "Please ensure the inventory backend API is running on port 8000"
            }
        
        # Process and enhance the summary data
        enhanced_summary = {
            "period_analyzed": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days_analyzed": days_back
            },
            "summary_statistics": wastage_summary,
            "business_insights": {
                "daily_average_cost": wastage_summary.get("total_cost", 0) / days_back if days_back > 0 else 0,
                "weekly_projection": (wastage_summary.get("total_cost", 0) / days_back) * 7 if days_back > 0 else 0,
                "monthly_projection": (wastage_summary.get("total_cost", 0) / days_back) * 30 if days_back > 0 else 0,
                "cost_impact": "High" if wastage_summary.get("total_cost", 0) > 1000 else "Medium" if wastage_summary.get("total_cost", 0) > 500 else "Low"
            }
        }
        
        # Add trend analysis if requested
        if include_trends:
            enhanced_summary["trend_analysis"] = {
                "primary_reasons": wastage_summary.get("wastage_by_reason", {}),
                "trend_direction": "Increasing" if wastage_summary.get("trend", 0) > 0 else "Decreasing" if wastage_summary.get("trend", 0) < 0 else "Stable",
                "seasonal_patterns": "Requires longer historical data for analysis"
            }
        
        # Add detailed cost analysis if requested
        if include_cost_analysis:
            total_cost = wastage_summary.get("total_cost", 0)
            enhanced_summary["cost_analysis"] = {
                "total_wastage_cost": total_cost,
                "cost_breakdown_by_reason": wastage_summary.get("cost_by_reason", {}),
                "cost_as_percentage": "Requires revenue data for percentage calculation",
                "recommendations": [
                    "Focus on expired items - implement better inventory rotation",
                    "Reduce damaged goods through better handling procedures",
                    "Investigate theft-related losses if significant",
                    "Implement portion control to reduce overproduction waste"
                ]
            }
        
        return {
            "success": True,
            "wastage_summary": enhanced_summary,
            "action_items": [
                "Review top wastage categories for immediate intervention",
                "Implement preventive measures for primary waste reasons",
                "Set up monitoring alerts for unusual wastage patterns",
                "Train staff on waste reduction best practices"
            ],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Wastage summary analysis failed: {str(e)}",
            "tool": "get_wastage_summary"
        }

@tool
def analyze_wastage_by_product(
    product_id: Optional[str] = None,
    reason_filter: Optional[str] = None,
    days_back: int = 30,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Analyze wastage patterns for specific products or reasons.
    
    Args:
        product_id: Specific product to analyze (optional)
        reason_filter: Filter by wastage reason (expired, damaged, theft, other)
        days_back: Number of days to analyze
        limit: Maximum number of records to return
    
    Returns:
        Detailed wastage analysis by product with patterns and insights
    """
    
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Build API parameters
        params = []
        if product_id:
            params.append(f"product_id={product_id}")
        if reason_filter:
            params.append(f"reason={reason_filter}")
        params.append(f"start_date={start_date.isoformat()}")
        params.append(f"end_date={end_date.isoformat()}")
        params.append(f"limit={limit}")
        
        query_string = "&".join(params)
        wastage_data = make_api_call(f"/api/v1/wastage?{query_string}")
        
        if wastage_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to connect to backend server: {wastage_data.get('message')}",
                "endpoint": "/api/v1/wastage",
                "suggestion": "Please ensure the inventory backend API is running on port 8000"
            }
        
        # Process wastage records
        wastage_records = wastage_data if isinstance(wastage_data, list) else wastage_data.get("records", [])
        
        # Analyze patterns
        product_analysis = {}
        reason_breakdown = {}
        total_cost = 0
        total_quantity = 0
        
        for record in wastage_records:
            product_name = record.get("product_name", "Unknown")
            reason = record.get("reason", "unknown")
            cost = float(record.get("cost", 0))
            quantity = float(record.get("quantity", 0))
            
            # Track by product
            if product_name not in product_analysis:
                product_analysis[product_name] = {
                    "total_cost": 0,
                    "total_quantity": 0,
                    "occurrences": 0,
                    "reasons": {}
                }
            
            product_analysis[product_name]["total_cost"] += cost
            product_analysis[product_name]["total_quantity"] += quantity
            product_analysis[product_name]["occurrences"] += 1
            
            if reason not in product_analysis[product_name]["reasons"]:
                product_analysis[product_name]["reasons"][reason] = 0
            product_analysis[product_name]["reasons"][reason] += 1
            
            # Track by reason
            if reason not in reason_breakdown:
                reason_breakdown[reason] = {"cost": 0, "quantity": 0, "count": 0}
            reason_breakdown[reason]["cost"] += cost
            reason_breakdown[reason]["quantity"] += quantity
            reason_breakdown[reason]["count"] += 1
            
            total_cost += cost
            total_quantity += quantity
        
        # Sort products by cost impact
        top_wastage_products = sorted(
            product_analysis.items(),
            key=lambda x: x[1]["total_cost"],
            reverse=True
        )
        
        return {
            "success": True,
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days_analyzed": days_back
            },
            "filters_applied": {
                "product_id": product_id,
                "reason_filter": reason_filter,
                "limit": limit
            },
            "overall_summary": {
                "total_records": len(wastage_records),
                "total_cost": total_cost,
                "total_quantity": total_quantity,
                "average_cost_per_incident": total_cost / len(wastage_records) if wastage_records else 0
            },
            "product_analysis": [
                {
                    "product_name": product,
                    "total_cost": analysis["total_cost"],
                    "total_quantity": analysis["total_quantity"],
                    "occurrences": analysis["occurrences"],
                    "average_cost_per_incident": analysis["total_cost"] / analysis["occurrences"],
                    "primary_reason": max(analysis["reasons"].items(), key=lambda x: x[1])[0] if analysis["reasons"] else "unknown",
                    "cost_percentage": (analysis["total_cost"] / total_cost * 100) if total_cost > 0 else 0
                }
                for product, analysis in top_wastage_products[:10]
            ],
            "reason_breakdown": reason_breakdown,
            "recommendations": [
                "Focus on top 3 products causing highest wastage costs",
                "Implement specific controls for primary wastage reasons",
                "Set up alerts for products with frequent wastage incidents",
                "Review inventory rotation practices for high-waste items"
            ],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Product wastage analysis failed: {str(e)}",
            "tool": "analyze_wastage_by_product"
        }

@tool
def track_wastage_trends(
    time_period: str = "monthly",
    months_back: int = 6
) -> Dict[str, Any]:
    """
    Track wastage trends over time to identify patterns and seasonal variations.
    
    Args:
        time_period: Analysis granularity (daily, weekly, monthly)
        months_back: Number of months of historical data to analyze
    
    Returns:
        Trend analysis with patterns, seasonality, and predictions
    """
    
    try:
        # Calculate analysis period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)  # Approximate months to days
        
        # Get comprehensive wastage data for trend analysis
        wastage_data = make_api_call(f"/api/v1/wastage?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}&limit=1000")
        
        if wastage_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to connect to backend server: {wastage_data.get('message')}",
                "endpoint": "/api/v1/wastage",
                "suggestion": "Please ensure the inventory backend API is running on port 8000"
            }
        
        # Process records for trend analysis
        wastage_records = wastage_data if isinstance(wastage_data, list) else wastage_data.get("records", [])
        
        # Group by time period
        time_series = {}
        monthly_breakdown = {}
        
        for record in wastage_records:
            recorded_date = record.get("recorded_at", record.get("created_at", ""))
            if recorded_date:
                try:
                    date_obj = datetime.fromisoformat(recorded_date.replace('Z', '+00:00'))
                    
                    # Monthly grouping
                    month_key = date_obj.strftime("%Y-%m")
                    if month_key not in monthly_breakdown:
                        monthly_breakdown[month_key] = {
                            "cost": 0,
                            "quantity": 0,
                            "incidents": 0,
                            "reasons": {}
                        }
                    
                    cost = float(record.get("cost", 0))
                    quantity = float(record.get("quantity", 0))
                    reason = record.get("reason", "unknown")
                    
                    monthly_breakdown[month_key]["cost"] += cost
                    monthly_breakdown[month_key]["quantity"] += quantity
                    monthly_breakdown[month_key]["incidents"] += 1
                    
                    if reason not in monthly_breakdown[month_key]["reasons"]:
                        monthly_breakdown[month_key]["reasons"][reason] = 0
                    monthly_breakdown[month_key]["reasons"][reason] += 1
                    
                except (ValueError, AttributeError):
                    continue
        
        # Calculate trends
        sorted_months = sorted(monthly_breakdown.keys())
        if len(sorted_months) >= 2:
            recent_avg = sum(monthly_breakdown[month]["cost"] for month in sorted_months[-3:]) / min(3, len(sorted_months))
            earlier_avg = sum(monthly_breakdown[month]["cost"] for month in sorted_months[:3]) / min(3, len(sorted_months))
            trend_direction = "Increasing" if recent_avg > earlier_avg else "Decreasing" if recent_avg < earlier_avg else "Stable"
        else:
            trend_direction = "Insufficient data"
            recent_avg = 0
            earlier_avg = 0
        
        return {
            "success": True,
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "months_analyzed": months_back
            },
            "trend_summary": {
                "overall_trend": trend_direction,
                "recent_monthly_average": recent_avg,
                "earlier_monthly_average": earlier_avg,
                "trend_percentage": ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
            },
            "monthly_breakdown": monthly_breakdown,
            "insights": {
                "peak_wastage_month": max(monthly_breakdown.items(), key=lambda x: x[1]["cost"])[0] if monthly_breakdown else "N/A",
                "lowest_wastage_month": min(monthly_breakdown.items(), key=lambda x: x[1]["cost"])[0] if monthly_breakdown else "N/A",
                "most_common_reason": "Requires detailed reason analysis",
                "seasonal_pattern": "Longer historical data needed for seasonal analysis"
            },
            "recommendations": [
                "Monitor monthly trends for early intervention opportunities",
                "Investigate factors causing peak wastage months",
                "Implement preventive measures during high-risk periods",
                "Set up automated alerts for unusual trend deviations"
            ],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Wastage trend analysis failed: {str(e)}",
            "tool": "track_wastage_trends"
        }
