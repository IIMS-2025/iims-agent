"""
Batch Tracking Tool for LangGraph
Tools for analyzing batch history, traceability, and inventory management
"""

from langchain_core.tools import tool
import requests
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

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
def get_batch_history(
    batch_id: str,
    include_transactions: bool = True,
    include_quality_metrics: bool = True
) -> Dict[str, Any]:
    """
    Get comprehensive batch history and transaction details for traceability.
    
    Args:
        batch_id: Specific batch ID to track
        include_transactions: Include all transaction history for the batch
        include_quality_metrics: Include quality and expiry information
    
    Returns:
        Complete batch history with transactions and quality analysis
    """
    
    try:
        batch_history = make_api_call(f"/api/v1/stock/batch/{batch_id}/history")
        
        if batch_history.get("error"):
            return {
                "error": True,
                "message": f"Unable to connect to backend server: {batch_history.get('message')}",
                "endpoint": f"/api/v1/stock/batch/{batch_id}/history",
                "suggestion": "Please ensure the inventory backend API is running on port 8000"
            }
        
        # Process batch history data
        transactions = batch_history if isinstance(batch_history, list) else [batch_history]
        
        # Analyze transactions
        transaction_analysis = {
            "total_transactions": len(transactions),
            "transaction_types": {},
            "quantity_flow": {
                "total_received": 0,
                "total_consumed": 0,
                "total_wasted": 0,
                "current_balance": 0
            },
            "timeline": [],
            "quality_events": []
        }
        
        # Sort transactions by date for timeline analysis
        sorted_transactions = sorted(
            transactions,
            key=lambda x: x.get("transaction_date", x.get("created_at", "")),
            reverse=False
        )
        
        running_balance = 0
        
        for transaction in sorted_transactions:
            transaction_type = transaction.get("transaction_type", "unknown")
            quantity = float(transaction.get("quantity", 0))
            transaction_date = transaction.get("transaction_date", transaction.get("created_at", ""))
            reason = transaction.get("reason", "")
            
            # Count transaction types
            transaction_analysis["transaction_types"][transaction_type] = \
                transaction_analysis["transaction_types"].get(transaction_type, 0) + 1
            
            # Track quantity flow
            if transaction_type in ["purchase", "receive", "production"]:
                transaction_analysis["quantity_flow"]["total_received"] += quantity
                running_balance += quantity
            elif transaction_type in ["sale", "consumption", "usage"]:
                transaction_analysis["quantity_flow"]["total_consumed"] += quantity
                running_balance -= quantity
            elif transaction_type in ["waste", "damage", "expiry"]:
                transaction_analysis["quantity_flow"]["total_wasted"] += quantity
                running_balance -= quantity
            
            # Timeline entry
            timeline_entry = {
                "date": transaction_date,
                "type": transaction_type,
                "quantity": quantity,
                "reason": reason,
                "running_balance": running_balance,
                "transaction_id": transaction.get("id", "")
            }
            transaction_analysis["timeline"].append(timeline_entry)
            
            # Quality events
            if transaction_type in ["waste", "damage", "expiry"] or "quality" in reason.lower():
                quality_event = {
                    "date": transaction_date,
                    "issue_type": transaction_type,
                    "quantity_affected": quantity,
                    "reason": reason,
                    "cost_impact": quantity * transaction.get("unit_cost", 0)
                }
                transaction_analysis["quality_events"].append(quality_event)
        
        transaction_analysis["quantity_flow"]["current_balance"] = running_balance
        
        # Calculate batch metrics
        batch_metrics = {
            "batch_utilization": (transaction_analysis["quantity_flow"]["total_consumed"] / 
                                transaction_analysis["quantity_flow"]["total_received"] * 100) \
                                if transaction_analysis["quantity_flow"]["total_received"] > 0 else 0,
            "waste_percentage": (transaction_analysis["quantity_flow"]["total_wasted"] / 
                               transaction_analysis["quantity_flow"]["total_received"] * 100) \
                               if transaction_analysis["quantity_flow"]["total_received"] > 0 else 0,
            "total_value_consumed": sum(float(t.get("quantity", 0)) * float(t.get("unit_cost", 0)) 
                                     for t in transactions if t.get("transaction_type") in ["sale", "consumption"]),
            "total_value_wasted": sum(float(t.get("quantity", 0)) * float(t.get("unit_cost", 0)) 
                                    for t in transactions if t.get("transaction_type") in ["waste", "damage"])
        }
        
        # Quality analysis
        quality_analysis = {}
        if include_quality_metrics:
            quality_analysis = {
                "quality_issues": len(transaction_analysis["quality_events"]),
                "primary_quality_concern": max([e["issue_type"] for e in transaction_analysis["quality_events"]], 
                                             default="None"),
                "quality_cost_impact": sum(e["cost_impact"] for e in transaction_analysis["quality_events"]),
                "quality_score": max(0, 100 - batch_metrics["waste_percentage"])
            }
        
        return {
            "success": True,
            "batch_id": batch_id,
            "transaction_analysis": transaction_analysis,
            "batch_metrics": batch_metrics,
            "quality_analysis": quality_analysis,
            "business_insights": {
                "batch_efficiency": "High" if batch_metrics["waste_percentage"] < 5 else 
                                  "Medium" if batch_metrics["waste_percentage"] < 15 else "Low",
                "traceability": "Complete" if len(transactions) > 0 else "Limited",
                "recommendations": [
                    "Monitor waste percentage - target below 5%",
                    "Investigate quality issues if waste is high",
                    "Improve handling if damage-related waste occurs",
                    "Optimize inventory rotation to reduce expiry waste"
                ]
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Batch history analysis failed: {str(e)}",
            "tool": "get_batch_history"
        }

@tool
def analyze_inventory_by_product(
    product_id: str,
    include_batch_details: bool = True,
    include_expiry_analysis: bool = True
) -> Dict[str, Any]:
    """
    Analyze inventory details for a specific product including all batches.
    
    Args:
        product_id: Product ID to analyze
        include_batch_details: Include detailed batch information
        include_expiry_analysis: Include expiry date analysis and alerts
    
    Returns:
        Comprehensive product inventory analysis with batch tracking
    """
    
    try:
        # Get inventory for specific product
        inventory_data = make_api_call(f"/api/v1/inventory/{product_id}")
        
        if inventory_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to connect to backend server: {inventory_data.get('message')}",
                "endpoint": f"/api/v1/inventory/{product_id}",
                "suggestion": "Please ensure the inventory backend API is running on port 8000"
            }
        
        # Also try the stock management endpoint
        stock_data = make_api_call(f"/api/v1/stock/inventory/{product_id}")
        
        # Process inventory data
        data_wrapper = inventory_data.get("data", [])
        if data_wrapper and len(data_wrapper) > 0:
            product_inventory = data_wrapper[0]
        else:
            product_inventory = inventory_data
        
        # Basic product information
        product_analysis = {
            "product_id": product_id,
            "name": product_inventory.get("name", "Unknown"),
            "type": product_inventory.get("type", "unknown"),
            "category": product_inventory.get("category", "uncategorized"),
            "total_quantity": float(product_inventory.get("available_qty", 0)),
            "unit": product_inventory.get("unit", ""),
            "current_status": product_inventory.get("stock_status", "unknown"),
            "last_updated": product_inventory.get("last_updated", ""),
            "has_recent_activity": product_inventory.get("has_recent_activity", False)
        }
        
        # Batch analysis
        batch_analysis = {}
        if include_batch_details and "batches" in product_inventory:
            batches = product_inventory.get("batches", [])
            
            batch_analysis = {
                "total_batches": len(batches),
                "batch_details": [],
                "quantity_by_batch": {},
                "expiry_distribution": {}
            }
            
            total_batch_quantity = 0
            expiry_dates = []
            
            for batch in batches:
                batch_info = {
                    "batch_id": batch.get("batch", ""),
                    "quantity": float(batch.get("total_qty", 0)),
                    "unit": batch.get("unit", ""),
                    "expiry_date": batch.get("expiry_date", ""),
                    "last_transaction": batch.get("last_transaction", ""),
                    "status": "active"  # Could be determined from expiry date
                }
                
                # Expiry analysis
                if batch.get("expiry_date"):
                    expiry_date = batch.get("expiry_date")
                    expiry_dates.append(expiry_date)
                    
                    # Determine expiry status
                    try:
                        expiry_dt = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
                        now = datetime.now(expiry_dt.tzinfo)
                        days_to_expiry = (expiry_dt - now).days
                        
                        if days_to_expiry < 0:
                            batch_info["expiry_status"] = "expired"
                        elif days_to_expiry <= 3:
                            batch_info["expiry_status"] = "critical"
                        elif days_to_expiry <= 7:
                            batch_info["expiry_status"] = "warning"
                        else:
                            batch_info["expiry_status"] = "good"
                        
                        batch_info["days_to_expiry"] = days_to_expiry
                    except (ValueError, AttributeError):
                        batch_info["expiry_status"] = "unknown"
                        batch_info["days_to_expiry"] = None
                
                batch_analysis["batch_details"].append(batch_info)
                batch_analysis["quantity_by_batch"][batch_info["batch_id"]] = batch_info["quantity"]
                total_batch_quantity += batch_info["quantity"]
            
            batch_analysis["total_quantity_in_batches"] = total_batch_quantity
            
            # Expiry analysis
            if include_expiry_analysis and expiry_dates:
                expiry_analysis = {
                    "earliest_expiry": min(expiry_dates),
                    "latest_expiry": max(expiry_dates),
                    "expired_batches": len([b for b in batch_analysis["batch_details"] 
                                          if b.get("expiry_status") == "expired"]),
                    "critical_batches": len([b for b in batch_analysis["batch_details"] 
                                           if b.get("expiry_status") == "critical"]),
                    "warning_batches": len([b for b in batch_analysis["batch_details"] 
                                          if b.get("expiry_status") == "warning"]),
                    "expiry_alerts": [
                        {
                            "batch_id": b["batch_id"],
                            "expiry_status": b["expiry_status"],
                            "days_to_expiry": b["days_to_expiry"],
                            "quantity": b["quantity"]
                        }
                        for b in batch_analysis["batch_details"]
                        if b.get("expiry_status") in ["expired", "critical", "warning"]
                    ]
                }
                
                product_analysis["expiry_analysis"] = expiry_analysis
        
        # Business insights
        business_insights = {
            "inventory_health": "Good" if product_analysis["current_status"] == "in_stock" else "Attention needed",
            "batch_management": "Well managed" if batch_analysis.get("total_batches", 0) > 0 else "Limited tracking",
            "expiry_risk": "Low" if not product_analysis.get("expiry_analysis", {}).get("critical_batches", 0) else "High",
            "recommendations": []
        }
        
        # Generate recommendations
        if product_analysis.get("expiry_analysis", {}).get("critical_batches", 0) > 0:
            business_insights["recommendations"].append("Prioritize usage of batches expiring soon")
        
        if product_analysis["current_status"] == "low_stock":
            business_insights["recommendations"].append("Consider reordering to maintain stock levels")
        
        if batch_analysis.get("total_batches", 0) > 5:
            business_insights["recommendations"].append("Review batch rotation practices to optimize freshness")
        
        return {
            "success": True,
            "product_analysis": product_analysis,
            "batch_analysis": batch_analysis,
            "business_insights": business_insights,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Product inventory analysis failed: {str(e)}",
            "tool": "analyze_inventory_by_product"
        }

@tool
def get_expiry_alerts(
    days_ahead: int = 7,
    include_expired: bool = True,
    severity_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get comprehensive expiry alerts across all inventory items.
    
    Args:
        days_ahead: Number of days ahead to check for expiring items
        include_expired: Include already expired items in the analysis
        severity_filter: Filter by severity (critical, warning, expired)
    
    Returns:
        Comprehensive expiry alerts with prioritization and action items
    """
    
    try:
        # Get all inventory to analyze expiry dates
        inventory_data = make_api_call("/api/v1/inventory")
        
        if inventory_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to connect to backend server: {inventory_data.get('message')}",
                "endpoint": "/api/v1/inventory",
                "suggestion": "Please ensure the inventory backend API is running on port 8000"
            }
        
        # Process inventory for expiry analysis
        inventory_items = inventory_data.get("ingredient_items", [])
        
        expiry_alerts = []
        now = datetime.now()
        
        for item in inventory_items:
            product_name = item.get("name", "Unknown")
            product_id = item.get("id", "")
            batches = item.get("batches", [])
            
            for batch in batches:
                expiry_date_str = batch.get("expiry_date")
                if expiry_date_str:
                    try:
                        expiry_date = datetime.fromisoformat(expiry_date_str.replace('Z', '+00:00'))
                        days_to_expiry = (expiry_date - now.replace(tzinfo=expiry_date.tzinfo)).days
                        
                        # Determine severity
                        if days_to_expiry < 0:
                            severity = "expired"
                            priority = 1
                        elif days_to_expiry <= 1:
                            severity = "critical"
                            priority = 2
                        elif days_to_expiry <= 3:
                            severity = "high"
                            priority = 3
                        elif days_to_expiry <= days_ahead:
                            severity = "warning"
                            priority = 4
                        else:
                            continue  # Not within alert timeframe
                        
                        # Apply severity filter
                        if severity_filter and severity != severity_filter:
                            continue
                        
                        # Skip expired items if not requested
                        if not include_expired and severity == "expired":
                            continue
                        
                        alert = {
                            "product_id": product_id,
                            "product_name": product_name,
                            "batch_id": batch.get("batch", ""),
                            "quantity": float(batch.get("total_qty", 0)),
                            "unit": batch.get("unit", ""),
                            "expiry_date": expiry_date_str,
                            "days_to_expiry": days_to_expiry,
                            "severity": severity,
                            "priority": priority,
                            "estimated_value": float(batch.get("total_qty", 0)) * float(item.get("price", 0)),
                            "last_transaction": batch.get("last_transaction", "")
                        }
                        
                        expiry_alerts.append(alert)
                        
                    except (ValueError, AttributeError):
                        continue
        
        # Sort alerts by priority and days to expiry
        expiry_alerts.sort(key=lambda x: (x["priority"], x["days_to_expiry"]))
        
        # Calculate summary statistics
        summary_stats = {
            "total_alerts": len(expiry_alerts),
            "expired_items": len([a for a in expiry_alerts if a["severity"] == "expired"]),
            "critical_items": len([a for a in expiry_alerts if a["severity"] == "critical"]),
            "high_priority_items": len([a for a in expiry_alerts if a["severity"] == "high"]),
            "warning_items": len([a for a in expiry_alerts if a["severity"] == "warning"]),
            "total_value_at_risk": sum(a["estimated_value"] for a in expiry_alerts),
            "expired_value": sum(a["estimated_value"] for a in expiry_alerts if a["severity"] == "expired")
        }
        
        # Generate action items
        action_items = []
        if summary_stats["expired_items"] > 0:
            action_items.append(f"Remove {summary_stats['expired_items']} expired items immediately")
        if summary_stats["critical_items"] > 0:
            action_items.append(f"Use {summary_stats['critical_items']} critical items within 24 hours")
        if summary_stats["high_priority_items"] > 0:
            action_items.append(f"Prioritize {summary_stats['high_priority_items']} items expiring in 1-3 days")
        if summary_stats["warning_items"] > 0:
            action_items.append(f"Plan usage for {summary_stats['warning_items']} items expiring within {days_ahead} days")
        
        return {
            "success": True,
            "analysis_parameters": {
                "days_ahead": days_ahead,
                "include_expired": include_expired,
                "severity_filter": severity_filter
            },
            "summary_statistics": summary_stats,
            "expiry_alerts": expiry_alerts,
            "action_items": action_items,
            "recommendations": [
                "Implement first-in-first-out (FIFO) inventory rotation",
                "Set up automated alerts for items approaching expiry",
                "Consider promotional pricing for items near expiry",
                "Review ordering patterns to reduce expiry waste",
                "Train staff on proper inventory rotation procedures"
            ],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Expiry alerts analysis failed: {str(e)}",
            "tool": "get_expiry_alerts"
        }
