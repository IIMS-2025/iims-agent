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
        # Use simple date format (YYYY-MM-DD) instead of full ISO format to avoid API encoding issues
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        wastage_summary = make_api_call(f"/api/v1/wastage/summary?start_date={start_date_str}&end_date={end_date_str}")
        
        # Check if API call returned an error (only if it's a dict)
        if isinstance(wastage_summary, dict) and wastage_summary.get("error"):
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
        # Use simple date format (YYYY-MM-DD) instead of full ISO format to avoid API encoding issues
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        params = []
        if product_id:
            params.append(f"product_id={product_id}")
        if reason_filter:
            params.append(f"reason={reason_filter}")
        params.append(f"start_date={start_date_str}")
        params.append(f"end_date={end_date_str}")
        params.append(f"limit={limit}")
        
        query_string = "&".join(params)
        wastage_data = make_api_call(f"/api/v1/wastage?{query_string}")
        
        # Check if API call returned an error (only if it's a dict)
        if isinstance(wastage_data, dict) and wastage_data.get("error"):
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
            # API returns different field names: cost_loss, qty
            cost = float(record.get("cost_loss", record.get("cost", 0)))
            quantity = float(record.get("qty", record.get("quantity", 0)))
            
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
        # Use simple date format (YYYY-MM-DD) instead of full ISO format to avoid API encoding issues
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        wastage_data = make_api_call(f"/api/v1/wastage?start_date={start_date_str}&end_date={end_date_str}&limit=200")
        
        # Check if API call returned an error (only if it's a dict)
        if isinstance(wastage_data, dict) and wastage_data.get("error"):
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
                    
                    # API returns different field names: cost_loss
                    cost = float(record.get("cost_loss", record.get("cost", 0)))
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

@tool
def get_wastage_trends(
    date_range: str = "last_30_days",
    group_by: str = "week"
) -> Dict[str, Any]:
    """
    Real wastage trend analysis from database using actual wastage records.
    
    Args:
        date_range: Time period to analyze (last_7_days, last_30_days, last_90_days)
        group_by: Grouping level (day, week, month)
    
    Returns:
        Trend analysis based on real wastage data with patterns and insights
    """
    
    try:
        # Calculate date range
        end_date = datetime.now()
        if date_range == "last_7_days":
            start_date = end_date - timedelta(days=7)
        elif date_range == "last_30_days":
            start_date = end_date - timedelta(days=30)
        elif date_range == "last_90_days":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)  # Default
            
        # Fetch real wastage data
        # Use simple date format (YYYY-MM-DD) instead of full ISO format to avoid API encoding issues
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        params = {
            "start_date": start_date_str,
            "end_date": end_date_str,
            "limit": 200  # Get comprehensive data for trend analysis
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        wastage_data = make_api_call(f"/api/v1/wastage?{query_string}")
        
        # Check if API call returned an error (only if it's a dict)
        if isinstance(wastage_data, dict) and wastage_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to fetch wastage data: {wastage_data.get('message')}",
                "endpoint": "/api/v1/wastage"
            }
        
        # Process wastage records for trend analysis
        wastage_records = wastage_data if isinstance(wastage_data, list) else wastage_data.get("records", [])
        
        # Group data by time period
        time_groups = {}
        reason_trends = {}
        cost_trends = {}
        
        for record in wastage_records:
            recorded_date = record.get("recorded_at", record.get("created_at", ""))
            if recorded_date:
                try:
                    date_obj = datetime.fromisoformat(recorded_date.replace('Z', '+00:00'))
                    
                    # Create time grouping key
                    if group_by == "day":
                        time_key = date_obj.strftime("%Y-%m-%d")
                    elif group_by == "week":
                        # Get week start (Monday)
                        week_start = date_obj - timedelta(days=date_obj.weekday())
                        time_key = week_start.strftime("%Y-%m-%d") + " (Week)"
                    else:  # month
                        time_key = date_obj.strftime("%Y-%m")
                    
                    # Initialize time group
                    if time_key not in time_groups:
                        time_groups[time_key] = {
                            "total_cost": 0,
                            "total_quantity": 0,
                            "incident_count": 0,
                            "reasons": {},
                            "products": {}
                        }
                    
                    # Aggregate data
                    # API returns different field names: cost_loss
                    cost = float(record.get("cost_loss", record.get("cost", 0)))
                    quantity = float(record.get("quantity", 0))
                    reason = record.get("reason", "unknown")
                    product_name = record.get("product_name", "Unknown")
                    
                    time_groups[time_key]["total_cost"] += cost
                    time_groups[time_key]["total_quantity"] += quantity
                    time_groups[time_key]["incident_count"] += 1
                    
                    # Track reasons
                    if reason not in time_groups[time_key]["reasons"]:
                        time_groups[time_key]["reasons"][reason] = 0
                    time_groups[time_key]["reasons"][reason] += 1
                    
                    # Track products
                    if product_name not in time_groups[time_key]["products"]:
                        time_groups[time_key]["products"][product_name] = 0
                    time_groups[time_key]["products"][product_name] += cost
                    
                    # Overall reason trends
                    if reason not in reason_trends:
                        reason_trends[reason] = []
                    reason_trends[reason].append({"date": time_key, "cost": cost})
                    
                except (ValueError, AttributeError):
                    continue
        
        # Calculate trend direction
        sorted_time_keys = sorted(time_groups.keys())
        if len(sorted_time_keys) >= 2:
            recent_period = sorted_time_keys[-1]
            earlier_period = sorted_time_keys[0]
            recent_cost = time_groups[recent_period]["total_cost"]
            earlier_cost = time_groups[earlier_period]["total_cost"]
            
            if recent_cost > earlier_cost * 1.1:
                trend_direction = "Increasing"
            elif recent_cost < earlier_cost * 0.9:
                trend_direction = "Decreasing"
            else:
                trend_direction = "Stable"
                
            trend_percentage = ((recent_cost - earlier_cost) / earlier_cost * 100) if earlier_cost > 0 else 0
        else:
            trend_direction = "Insufficient data"
            trend_percentage = 0
        
        # Peak and low periods
        if time_groups:
            peak_period = max(time_groups.items(), key=lambda x: x[1]["total_cost"])
            low_period = min(time_groups.items(), key=lambda x: x[1]["total_cost"])
        else:
            peak_period = ("N/A", {"total_cost": 0})
            low_period = ("N/A", {"total_cost": 0})
        
        # Top reasons across all periods
        overall_reasons = {}
        for group in time_groups.values():
            for reason, count in group["reasons"].items():
                overall_reasons[reason] = overall_reasons.get(reason, 0) + count
        
        top_reasons = sorted(overall_reasons.items(), key=lambda x: x[1], reverse=True)[:5]
        
        trends_result = {
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "date_range": date_range,
                "group_by": group_by,
                "total_periods": len(time_groups)
            },
            "overall_trends": {
                "trend_direction": trend_direction,
                "trend_percentage": round(trend_percentage, 2),
                "total_wastage_cost": sum(group["total_cost"] for group in time_groups.values()),
                "total_incidents": sum(group["incident_count"] for group in time_groups.values()),
                "average_cost_per_period": round(sum(group["total_cost"] for group in time_groups.values()) / len(time_groups), 2) if time_groups else 0
            },
            "period_breakdown": {
                time_key: {
                    "total_cost": round(data["total_cost"], 2),
                    "incident_count": data["incident_count"],
                    "top_reason": max(data["reasons"].items(), key=lambda x: x[1])[0] if data["reasons"] else "unknown",
                    "top_product": max(data["products"].items(), key=lambda x: x[1])[0] if data["products"] else "unknown"
                }
                for time_key, data in sorted(time_groups.items())
            },
            "peak_analysis": {
                "highest_cost_period": peak_period[0],
                "highest_cost_amount": round(peak_period[1]["total_cost"], 2),
                "lowest_cost_period": low_period[0],
                "lowest_cost_amount": round(low_period[1]["total_cost"], 2)
            },
            "reason_analysis": {
                "top_reasons": [{"reason": reason, "occurrences": count} for reason, count in top_reasons],
                "reason_trends": "Detailed reason trending available in period breakdown"
            },
            "insights": []
        }
        
        # Add insights based on trend analysis
        if trend_direction == "Increasing":
            trends_result["insights"].append(f"Wastage costs increasing by {abs(trend_percentage):.1f}% - requires immediate attention")
        elif trend_direction == "Decreasing":
            trends_result["insights"].append(f"Positive trend: wastage costs decreasing by {abs(trend_percentage):.1f}%")
        
        if peak_period[1]["total_cost"] > low_period[1]["total_cost"] * 2:
            trends_result["insights"].append("High variance in wastage costs - investigate peak periods")
        
        if top_reasons and top_reasons[0][1] > sum(count for _, count in top_reasons[1:]):
            trends_result["insights"].append(f"Primary wastage reason: {top_reasons[0][0]} - focus intervention here")
            
        return {
            "success": True,
            "trends": trends_result,
            "data_source": f"Real wastage trends from /api/v1/wastage ({len(wastage_records)} records)",
            "confidence": "High - Based on actual wastage events",
            "source_endpoints": ["/api/v1/wastage"],
            "calculation_method": f"Time-series analysis grouped by {group_by} from real wastage data",
            "data_freshness": "Real-time",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Wastage trends analysis failed: {str(e)}",
            "tool": "get_wastage_trends"
        }

@tool
def get_top_wastage_products(
    limit: int = 10,
    date_range: str = "last_30_days"
) -> Dict[str, Any]:
    """
    Top wastage products from live data ranked by actual wastage costs.
    
    Args:
        limit: Number of top products to return
        date_range: Time period for analysis
    
    Returns:
        Product rankings based on real wastage data with cost and frequency analysis
    """
    
    try:
        # Calculate date range
        end_date = datetime.now()
        if date_range == "last_7_days":
            start_date = end_date - timedelta(days=7)
        elif date_range == "last_30_days":
            start_date = end_date - timedelta(days=30)
        elif date_range == "last_90_days":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)
            
        # Fetch wastage data
        # Use simple date format (YYYY-MM-DD) instead of full ISO format to avoid API encoding issues
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        params = {
            "start_date": start_date_str,
            "end_date": end_date_str,
            "limit": 200
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        wastage_data = make_api_call(f"/api/v1/wastage?{query_string}")
        
        # Check if API call returned an error (only if it's a dict)
        if isinstance(wastage_data, dict) and wastage_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to fetch wastage data: {wastage_data.get('message')}",
                "endpoint": "/api/v1/wastage"
            }
        
        wastage_records = wastage_data if isinstance(wastage_data, list) else wastage_data.get("records", [])
        
        # Aggregate by product
        product_wastage = {}
        
        for record in wastage_records:
            # API returns different field names: cost_loss, qty, inventory_id
            product_name = record.get("product_name", record.get("inventory_id", "Unknown Product"))
            cost = float(record.get("cost_loss", record.get("cost", 0)))
            quantity = float(record.get("qty", record.get("quantity", 0)))
            reason = record.get("reason", "unknown")
            
            if product_name not in product_wastage:
                product_wastage[product_name] = {
                    "total_cost": 0,
                    "total_quantity": 0,
                    "incident_count": 0,
                    "reasons": {},
                    "dates": []
                }
            
            product_wastage[product_name]["total_cost"] += cost
            product_wastage[product_name]["total_quantity"] += quantity
            product_wastage[product_name]["incident_count"] += 1
            
            # Track reasons
            if reason not in product_wastage[product_name]["reasons"]:
                product_wastage[product_name]["reasons"][reason] = 0
            product_wastage[product_name]["reasons"][reason] += 1
            
            # Track dates for frequency analysis
            recorded_date = record.get("recorded_at", record.get("created_at", ""))
            if recorded_date:
                product_wastage[product_name]["dates"].append(recorded_date)
        
        # Calculate additional metrics and rank products
        ranked_products = []
        
        for product_name, data in product_wastage.items():
            # Calculate average cost per incident
            avg_cost_per_incident = data["total_cost"] / data["incident_count"] if data["incident_count"] > 0 else 0
            
            # Most common reason
            top_reason = max(data["reasons"].items(), key=lambda x: x[1])[0] if data["reasons"] else "unknown"
            
            # Frequency analysis
            if data["dates"]:
                # Calculate days between incidents
                sorted_dates = sorted(data["dates"])
                if len(sorted_dates) > 1:
                    try:
                        first_date = datetime.fromisoformat(sorted_dates[0].replace('Z', '+00:00'))
                        last_date = datetime.fromisoformat(sorted_dates[-1].replace('Z', '+00:00'))
                        days_span = (last_date - first_date).days
                        frequency = data["incident_count"] / max(days_span, 1)  # incidents per day
                    except (ValueError, AttributeError):
                        frequency = 0
                else:
                    frequency = 0
            else:
                frequency = 0
            
            # Create product analysis
            product_analysis = {
                "product_name": product_name,
                "total_cost": round(data["total_cost"], 2),
                "total_quantity": round(data["total_quantity"], 2),
                "incident_count": data["incident_count"],
                "average_cost_per_incident": round(avg_cost_per_incident, 2),
                "primary_reason": top_reason,
                "frequency_per_day": round(frequency, 3),
                "cost_rank": 0,  # Will be set after sorting
                "reasons_breakdown": dict(data["reasons"]),
                "severity": "High" if data["total_cost"] > 100 else "Medium" if data["total_cost"] > 50 else "Low"
            }
            
            ranked_products.append(product_analysis)
        
        # Sort by total cost and assign ranks
        ranked_products.sort(key=lambda x: x["total_cost"], reverse=True)
        for i, product in enumerate(ranked_products[:limit]):
            product["cost_rank"] = i + 1
        
        # Calculate summary statistics
        total_products_analyzed = len(product_wastage)
        total_cost_all_products = sum(p["total_cost"] for p in ranked_products)
        top_products_subset = ranked_products[:limit]
        top_products_cost = sum(p["total_cost"] for p in top_products_subset)
        
        # Identify patterns
        high_frequency_products = [p for p in top_products_subset if p["frequency_per_day"] > 0.1]
        high_cost_products = [p for p in top_products_subset if p["total_cost"] > 100]
        
        # Reason analysis across top products
        reason_summary = {}
        for product in top_products_subset:
            for reason, count in product["reasons_breakdown"].items():
                reason_summary[reason] = reason_summary.get(reason, 0) + count
        
        top_reasons = sorted(reason_summary.items(), key=lambda x: x[1], reverse=True)[:5]
        
        result = {
            "analysis_summary": {
                "total_products_with_wastage": total_products_analyzed,
                "analysis_period": f"{date_range} ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})",
                "total_wastage_cost": round(total_cost_all_products, 2),
                "top_products_count": len(top_products_subset),
                "top_products_cost": round(top_products_cost, 2),
                "top_products_percentage": round((top_products_cost / total_cost_all_products * 100), 2) if total_cost_all_products > 0 else 0
            },
            "top_wastage_products": top_products_subset,
            "insights": {
                "high_frequency_products": len(high_frequency_products),
                "high_cost_products": len(high_cost_products),
                "top_reasons_across_products": [{"reason": reason, "occurrences": count} for reason, count in top_reasons],
                "patterns": []
            },
            "recommendations": []
        }
        
        # Add pattern insights
        if len(high_frequency_products) > 0:
            result["insights"]["patterns"].append(f"{len(high_frequency_products)} products have high wastage frequency")
        
        if top_products_cost / total_cost_all_products > 0.8:
            result["insights"]["patterns"].append("Top products account for majority of wastage costs - focus intervention here")
        
        # Add recommendations
        if top_products_subset:
            worst_product = top_products_subset[0]
            result["recommendations"].append(f"Priority: Address '{worst_product['product_name']}' - ${worst_product['total_cost']:.2f} in wastage")
            result["recommendations"].append(f"Focus on '{worst_product['primary_reason']}' issues for top wastage products")
        
        if len(high_frequency_products) > 2:
            result["recommendations"].append("Implement daily monitoring for high-frequency wastage products")
        
        if top_reasons and top_reasons[0][1] > 5:
            result["recommendations"].append(f"Address root cause: '{top_reasons[0][0]}' is the primary wastage reason")
            
        return {
            "success": True,
            "wastage_analysis": result,
            "data_source": f"Real product wastage from /api/v1/wastage ({len(wastage_records)} records)",
            "confidence": "High - Ranked by actual wastage costs",
            "source_endpoints": ["/api/v1/wastage"],
            "calculation_method": "Product aggregation and ranking from real wastage events",
            "data_freshness": "Real-time",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Top wastage products analysis failed: {str(e)}",
            "tool": "get_top_wastage_products"
        }

@tool
def get_wastage_by_date(date: str) -> Dict[str, Any]:
    """
    Date-specific wastage analysis using real data from wastage records.
    
    Args:
        date: Specific date to analyze (YYYY-MM-DD format)
    
    Returns:
        Detailed wastage analysis for the specified date with comparisons
    """
    
    try:
        # Parse the target date
        try:
            target_date = datetime.fromisoformat(date)
        except ValueError:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                return {
                    "error": True,
                    "message": f"Invalid date format: {date}. Use YYYY-MM-DD format",
                    "tool": "get_wastage_by_date"
                }
        
        # Set date range for the specific day
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        # Fetch wastage data for the specific date
        # Use simple date format (YYYY-MM-DD) instead of full ISO format to avoid API encoding issues
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        params = {
            "start_date": start_date_str,
            "end_date": end_date_str,
            "limit": 200
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        wastage_data = make_api_call(f"/api/v1/wastage?{query_string}")
        
        # Check if API call returned an error (only if it's a dict)
        if isinstance(wastage_data, dict) and wastage_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to fetch wastage data: {wastage_data.get('message')}",
                "endpoint": "/api/v1/wastage"
            }
        
        wastage_records = wastage_data if isinstance(wastage_data, list) else wastage_data.get("records", [])
        
        # Also get data for comparison (previous 7 days)
        comparison_start = start_date - timedelta(days=7)
        comparison_end = start_date
        
        # Use simple date format (YYYY-MM-DD) instead of full ISO format to avoid API encoding issues
        comparison_start_str = comparison_start.strftime("%Y-%m-%d")
        comparison_end_str = comparison_end.strftime("%Y-%m-%d")
        
        comparison_params = {
            "start_date": comparison_start_str,
            "end_date": comparison_end_str,
            "limit": 200
        }
        
        comparison_query = "&".join([f"{k}={v}" for k, v in comparison_params.items()])
        comparison_data = make_api_call(f"/api/v1/wastage?{comparison_query}")
        
        comparison_records = []
        if not comparison_data.get("error"):
            comparison_records = comparison_data if isinstance(comparison_data, list) else comparison_data.get("records", [])
        
        # Analyze target date wastage
        total_cost = 0
        total_quantity = 0
        incidents_count = len(wastage_records)
        reasons_breakdown = {}
        products_breakdown = {}
        hourly_breakdown = {}
        
        for record in wastage_records:
            # API returns different field names: cost_loss, qty
            cost = float(record.get("cost_loss", record.get("cost", 0)))
            quantity = float(record.get("qty", record.get("quantity", 0)))
            reason = record.get("reason", "unknown")
            product_name = record.get("product_name", "Unknown")
            recorded_time = record.get("recorded_at", record.get("created_at", ""))
            
            total_cost += cost
            total_quantity += quantity
            
            # Reason breakdown
            reasons_breakdown[reason] = reasons_breakdown.get(reason, 0) + 1
            
            # Product breakdown
            if product_name not in products_breakdown:
                products_breakdown[product_name] = {"cost": 0, "quantity": 0, "count": 0}
            products_breakdown[product_name]["cost"] += cost
            products_breakdown[product_name]["quantity"] += quantity
            products_breakdown[product_name]["count"] += 1
            
            # Hourly breakdown
            if recorded_time:
                try:
                    time_obj = datetime.fromisoformat(recorded_time.replace('Z', '+00:00'))
                    hour = time_obj.hour
                    hourly_breakdown[hour] = hourly_breakdown.get(hour, 0) + cost
                except (ValueError, AttributeError):
                    pass
        
        # Calculate comparison metrics
        comparison_total_cost = sum(float(r.get("cost", 0)) for r in comparison_records)
        comparison_incidents = len(comparison_records)
        comparison_avg_daily_cost = comparison_total_cost / 7 if comparison_records else 0
        comparison_avg_daily_incidents = comparison_incidents / 7 if comparison_records else 0
        
        # Performance vs average
        cost_vs_average = ((total_cost - comparison_avg_daily_cost) / comparison_avg_daily_cost * 100) if comparison_avg_daily_cost > 0 else 0
        incidents_vs_average = ((incidents_count - comparison_avg_daily_incidents) / comparison_avg_daily_incidents * 100) if comparison_avg_daily_incidents > 0 else 0
        
        # Top products and reasons
        top_products = sorted(products_breakdown.items(), key=lambda x: x[1]["cost"], reverse=True)[:5]
        top_reasons = sorted(reasons_breakdown.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Peak hour analysis
        peak_hour = max(hourly_breakdown.items(), key=lambda x: x[1])[0] if hourly_breakdown else None
        peak_hour_cost = hourly_breakdown.get(peak_hour, 0) if peak_hour is not None else 0
        
        date_analysis = {
            "target_date": date,
            "daily_summary": {
                "total_cost": round(total_cost, 2),
                "total_quantity": round(total_quantity, 2),
                "incidents_count": incidents_count,
                "average_cost_per_incident": round(total_cost / incidents_count, 2) if incidents_count > 0 else 0
            },
            "comparison_with_recent_average": {
                "previous_7_days_avg_cost": round(comparison_avg_daily_cost, 2),
                "previous_7_days_avg_incidents": round(comparison_avg_daily_incidents, 2),
                "cost_variance_percentage": round(cost_vs_average, 2),
                "incidents_variance_percentage": round(incidents_vs_average, 2),
                "performance": "Above average" if cost_vs_average > 10 else "Below average" if cost_vs_average < -10 else "Normal"
            },
            "breakdown_analysis": {
                "top_products": [
                    {
                        "product": product,
                        "cost": round(data["cost"], 2),
                        "incidents": data["count"],
                        "percentage_of_daily_cost": round((data["cost"] / total_cost * 100), 2) if total_cost > 0 else 0
                    }
                    for product, data in top_products
                ],
                "top_reasons": [
                    {
                        "reason": reason,
                        "incidents": count,
                        "percentage": round((count / incidents_count * 100), 2) if incidents_count > 0 else 0
                    }
                    for reason, count in top_reasons
                ]
            },
            "time_analysis": {
                "peak_hour": peak_hour,
                "peak_hour_cost": round(peak_hour_cost, 2) if peak_hour_cost else 0,
                "hourly_distribution": {str(hour): round(cost, 2) for hour, cost in sorted(hourly_breakdown.items())}
            },
            "insights": []
        }
        
        # Add insights based on analysis
        if cost_vs_average > 50:
            date_analysis["insights"].append("Significantly high wastage cost compared to recent average")
        elif cost_vs_average < -30:
            date_analysis["insights"].append("Lower than average wastage - good performance day")
        
        if incidents_count > comparison_avg_daily_incidents * 2:
            date_analysis["insights"].append("High number of wastage incidents - potential operational issues")
        
        if peak_hour is not None:
            if 11 <= peak_hour <= 14:
                date_analysis["insights"].append("Peak wastage during lunch hours - review food preparation")
            elif 18 <= peak_hour <= 21:
                date_analysis["insights"].append("Peak wastage during dinner hours - review portion control")
        
        if top_products and top_products[0][1]["cost"] / total_cost > 0.5:
            date_analysis["insights"].append(f"Single product '{top_products[0][0]}' accounts for majority of wastage")
            
        return {
            "success": True,
            "date_analysis": date_analysis,
            "data_source": f"Real wastage data from /api/v1/wastage for {date} ({len(wastage_records)} records)",
            "confidence": "High - Actual daily wastage data",
            "source_endpoints": ["/api/v1/wastage"],
            "calculation_method": "Daily aggregation with 7-day average comparison",
            "data_freshness": "Real-time",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Date-specific wastage analysis failed: {str(e)}",
            "tool": "get_wastage_by_date"
        }
