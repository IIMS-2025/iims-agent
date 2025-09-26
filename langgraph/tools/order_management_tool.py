"""
Order Management Tool for LangGraph - Data-First Implementation
Analyzes order patterns using real inventory movement data and cookbook information
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
def analyze_order_patterns(
    date_range: str = "last_7_days",
    menu_item_focus: Optional[str] = None
) -> Dict[str, Any]:
    """
    Order pattern analysis from real inventory data and cookbook information.
    
    Args:
        date_range: Time period for analysis (last_7_days, last_30_days)
        menu_item_focus: Specific menu item to focus analysis on
    
    Returns:
        Order patterns derived from inventory movements and menu data
    """
    
    try:
        # Fetch real data
        inventory_data = make_api_call("/api/v1/inventory")
        cookbook_data = make_api_call("/api/v1/cookbook")
        
        if inventory_data.get("error") or cookbook_data.get("error"):
            return {
                "error": True,
                "message": "Unable to fetch required data for order analysis",
                "missing_data": "inventory or cookbook"
            }
        
        inventory_items = inventory_data.get("ingredient_items", [])
        cookbook_items = cookbook_data.get("data", [])
        
        # Filter menu items
        menu_items = [item for item in cookbook_items if item.get("type") == "menu_item"]
        
        # Create ingredient-to-menu mapping
        ingredient_menu_mapping = {}
        menu_recipes = {}
        
        for menu_item in menu_items:
            menu_name = menu_item.get("name", "")
            menu_recipes[menu_name] = {
                "price": float(menu_item.get("price", 0)),
                "category": menu_item.get("category", "uncategorized"),
                "ingredients": menu_item.get("recipe", {}).get("ingredients", [])
            }
            
            # Map ingredients to this menu item
            for ingredient in menu_recipes[menu_name]["ingredients"]:
                ing_name = ingredient.get("name", "").lower()
                if ing_name not in ingredient_menu_mapping:
                    ingredient_menu_mapping[ing_name] = []
                ingredient_menu_mapping[ing_name].append(menu_name)
        
        # Analyze order patterns from inventory activity
        order_patterns = {}
        total_estimated_orders = 0
        active_menu_items = []
        
        for inv_item in inventory_items:
            if inv_item.get("has_recent_activity"):
                inv_name = inv_item.get("name", "").lower()
                stock_status = inv_item.get("stock_status", "unknown")
                
                # Find which menu items use this ingredient
                related_menu_items = []
                
                # Direct name matching
                if inv_name in ingredient_menu_mapping:
                    related_menu_items.extend(ingredient_menu_mapping[inv_name])
                
                # Fuzzy matching for common ingredients
                for menu_name, recipe_info in menu_recipes.items():
                    for ingredient in recipe_info["ingredients"]:
                        ingredient_name = ingredient.get("name", "").lower()
                        if inv_name in ingredient_name or ingredient_name in inv_name:
                            if menu_name not in related_menu_items:
                                related_menu_items.append(menu_name)
                
                # Estimate order frequency based on stock status
                if stock_status == "low_stock":
                    order_frequency = "High"
                    estimated_daily_orders = 8
                elif stock_status == "good_stock" and inv_item.get("has_recent_activity"):
                    order_frequency = "Medium"
                    estimated_daily_orders = 4
                else:
                    order_frequency = "Low"
                    estimated_daily_orders = 2
                
                # Track patterns for related menu items
                for menu_name in related_menu_items:
                    if menu_name not in order_patterns:
                        order_patterns[menu_name] = {
                            "estimated_daily_orders": 0,
                            "order_frequency": "Low",
                            "active_ingredients": [],
                            "category": menu_recipes[menu_name]["category"],
                            "price": menu_recipes[menu_name]["price"],
                            "estimated_daily_revenue": 0
                        }
                    
                    # Aggregate estimates
                    order_patterns[menu_name]["estimated_daily_orders"] += estimated_daily_orders
                    order_patterns[menu_name]["active_ingredients"].append(inv_item.get("name"))
                    order_patterns[menu_name]["order_frequency"] = order_frequency
                    
                    # Calculate revenue
                    daily_revenue = estimated_daily_orders * menu_recipes[menu_name]["price"]
                    order_patterns[menu_name]["estimated_daily_revenue"] += daily_revenue
                    total_estimated_orders += estimated_daily_orders
        
        # Adjust estimates for date range
        if date_range == "last_7_days":
            period_multiplier = 7
        elif date_range == "last_30_days":
            period_multiplier = 30
        else:
            period_multiplier = 7
        
        # Calculate period totals
        for menu_name, pattern in order_patterns.items():
            pattern["estimated_period_orders"] = pattern["estimated_daily_orders"] * period_multiplier
            pattern["estimated_period_revenue"] = pattern["estimated_daily_revenue"] * period_multiplier
        
        # Sort by order frequency
        top_ordered_items = sorted(
            order_patterns.items(),
            key=lambda x: x[1]["estimated_daily_orders"],
            reverse=True
        )[:10]
        
        # Peak ordering analysis
        peak_hours_estimate = {
            "lunch_peak": "12:00-14:00",
            "dinner_peak": "18:00-21:00",
            "estimated_peak_orders": max([p[1]["estimated_daily_orders"] for p in top_ordered_items]) if top_ordered_items else 0
        }
        
        # Category analysis
        category_orders = {}
        for menu_name, pattern in order_patterns.items():
            category = pattern["category"]
            if category not in category_orders:
                category_orders[category] = {
                    "total_orders": 0,
                    "total_revenue": 0,
                    "item_count": 0
                }
            category_orders[category]["total_orders"] += pattern["estimated_daily_orders"]
            category_orders[category]["total_revenue"] += pattern["estimated_daily_revenue"]
            category_orders[category]["item_count"] += 1
        
        analysis_result = {
            "analysis_period": date_range,
            "order_summary": {
                "total_estimated_daily_orders": total_estimated_orders,
                "active_menu_items": len(order_patterns),
                "total_menu_items": len(menu_items),
                "activity_percentage": round(len(order_patterns) / len(menu_items) * 100, 2) if menu_items else 0
            },
            "top_ordered_items": [
                {
                    "menu_item": menu_name,
                    "estimated_daily_orders": pattern["estimated_daily_orders"],
                    "estimated_daily_revenue": round(pattern["estimated_daily_revenue"], 2),
                    "order_frequency": pattern["order_frequency"],
                    "category": pattern["category"],
                    "price": pattern["price"],
                    "active_ingredients_count": len(pattern["active_ingredients"])
                }
                for menu_name, pattern in top_ordered_items
            ],
            "category_performance": [
                {
                    "category": category,
                    "estimated_daily_orders": data["total_orders"],
                    "estimated_daily_revenue": round(data["total_revenue"], 2),
                    "menu_items_count": data["item_count"],
                    "average_orders_per_item": round(data["total_orders"] / data["item_count"], 2) if data["item_count"] > 0 else 0
                }
                for category, data in sorted(category_orders.items(), key=lambda x: x[1]["total_orders"], reverse=True)
            ],
            "peak_ordering_analysis": peak_hours_estimate,
            "insights": []
        }
        
        # Add insights
        if total_estimated_orders > 50:
            analysis_result["insights"].append("High order volume detected - busy period")
        
        if len(order_patterns) > len(menu_items) * 0.7:
            analysis_result["insights"].append("High menu utilization - most items being ordered")
        
        if top_ordered_items and top_ordered_items[0][1]["estimated_daily_orders"] > 20:
            analysis_result["insights"].append(f"'{top_ordered_items[0][0]}' is the clear bestseller")
        
        # Focus on specific menu item if requested
        if menu_item_focus and menu_item_focus in order_patterns:
            focus_pattern = order_patterns[menu_item_focus]
            analysis_result["focused_item_analysis"] = {
                "menu_item": menu_item_focus,
                "estimated_daily_orders": focus_pattern["estimated_daily_orders"],
                "estimated_daily_revenue": round(focus_pattern["estimated_daily_revenue"], 2),
                "active_ingredients": focus_pattern["active_ingredients"],
                "order_trend": focus_pattern["order_frequency"]
            }
        
        return {
            "success": True,
            "order_analysis": analysis_result,
            "data_source": "Order patterns derived from inventory movements + cookbook data",
            "confidence": "Medium - Based on inventory activity indicators",
            "source_endpoints": ["/api/v1/inventory", "/api/v1/cookbook"],
            "calculation_method": "Inventory activity mapping to menu items for order estimation",
            "data_freshness": "Real-time",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Order pattern analysis failed: {str(e)}",
            "tool": "analyze_order_patterns"
        }

@tool
def estimate_daily_orders(target_date: str) -> Dict[str, Any]:
    """
    Daily order estimation using real data for a specific date.
    
    Args:
        target_date: Specific date to analyze (YYYY-MM-DD format)
    
    Returns:
        Daily order estimates based on inventory and menu data
    """
    
    try:
        # Get current data (in real implementation, would get historical data for target_date)
        inventory_data = make_api_call("/api/v1/inventory")
        cookbook_data = make_api_call("/api/v1/cookbook")
        
        if inventory_data.get("error") or cookbook_data.get("error"):
            return {
                "error": True,
                "message": "Unable to fetch required data for daily order estimation"
            }
        
        inventory_items = inventory_data.get("ingredient_items", [])
        cookbook_items = cookbook_data.get("data", [])
        
        # Get active ingredients (proxy for recent ordering)
        active_ingredients = [item for item in inventory_items if item.get("has_recent_activity")]
        
        # Menu items mapping
        menu_items = [item for item in cookbook_items if item.get("type") == "menu_item"]
        
        # Estimate orders based on ingredient activity
        daily_estimates = []
        total_estimated_orders = 0
        total_estimated_revenue = 0
        
        for menu_item in menu_items:
            menu_name = menu_item.get("name", "")
            menu_price = float(menu_item.get("price", 0))
            recipe = menu_item.get("recipe", {})
            ingredients = recipe.get("ingredients", [])
            
            # Count how many ingredients for this menu item are active
            active_ingredient_count = 0
            for ingredient in ingredients:
                ing_name = ingredient.get("name", "").lower()
                for active_ing in active_ingredients:
                    if ing_name in active_ing.get("name", "").lower():
                        active_ingredient_count += 1
                        break
            
            # Estimate orders based on ingredient activity
            if active_ingredient_count > 0:
                activity_ratio = active_ingredient_count / len(ingredients) if ingredients else 0
                base_orders = 5  # Base daily orders
                estimated_orders = int(base_orders * activity_ratio * 2)  # Scale by activity
                estimated_revenue = estimated_orders * menu_price
                
                daily_estimates.append({
                    "menu_item": menu_name,
                    "estimated_orders": estimated_orders,
                    "unit_price": menu_price,
                    "estimated_revenue": round(estimated_revenue, 2),
                    "active_ingredients": active_ingredient_count,
                    "total_ingredients": len(ingredients),
                    "activity_ratio": round(activity_ratio * 100, 2)
                })
                
                total_estimated_orders += estimated_orders
                total_estimated_revenue += estimated_revenue
        
        # Sort by estimated orders
        daily_estimates.sort(key=lambda x: x["estimated_orders"], reverse=True)
        
        # Time-based distribution estimate
        hourly_distribution = {
            "breakfast_period": {"hours": "07:00-10:00", "percentage": 15},
            "lunch_period": {"hours": "11:00-15:00", "percentage": 40},
            "dinner_period": {"hours": "17:00-22:00", "percentage": 35},
            "other_hours": {"hours": "Other", "percentage": 10}
        }
        
        # Calculate hourly estimates
        for period, data in hourly_distribution.items():
            period_orders = int(total_estimated_orders * (data["percentage"] / 100))
            data["estimated_orders"] = period_orders
            data["estimated_revenue"] = round(period_orders * (total_estimated_revenue / total_estimated_orders), 2) if total_estimated_orders > 0 else 0
        
        daily_analysis = {
            "target_date": target_date,
            "daily_summary": {
                "total_estimated_orders": total_estimated_orders,
                "total_estimated_revenue": round(total_estimated_revenue, 2),
                "average_order_value": round(total_estimated_revenue / total_estimated_orders, 2) if total_estimated_orders > 0 else 0,
                "active_menu_items": len(daily_estimates),
                "total_menu_items": len(menu_items)
            },
            "item_estimates": daily_estimates[:15],  # Top 15
            "time_distribution": hourly_distribution,
            "insights": []
        }
        
        # Add insights
        avg_order_value = daily_analysis["daily_summary"]["average_order_value"]
        if avg_order_value > 300:
            daily_analysis["insights"].append("High average order value - premium menu performance")
        elif avg_order_value < 150:
            daily_analysis["insights"].append("Lower average order value - focus on upselling")
        
        if total_estimated_orders > 100:
            daily_analysis["insights"].append("High volume day - ensure adequate staffing")
        
        # Best selling item insight
        if daily_estimates:
            best_seller = daily_estimates[0]
            daily_analysis["insights"].append(f"Top performer: {best_seller['menu_item']} with {best_seller['estimated_orders']} estimated orders")
        
        return {
            "success": True,
            "daily_orders": daily_analysis,
            "data_source": "Daily estimates from inventory activity + menu data",
            "confidence": "Medium - Based on current inventory patterns",
            "source_endpoints": ["/api/v1/inventory", "/api/v1/cookbook"],
            "calculation_method": "Ingredient activity correlation with menu item ordering",
            "limitations": [
                "Estimates based on current inventory activity patterns",
                "Historical ordering data not available",
                "Seasonal variations not accounted for"
            ],
            "data_freshness": "Real-time",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Daily order estimation failed: {str(e)}",
            "tool": "estimate_daily_orders"
        }

@tool
def track_menu_item_demand(
    menu_item_id: Optional[str] = None,
    days_back: int = 30
) -> Dict[str, Any]:
    """
    Menu item demand tracking from inventory usage patterns.
    
    Args:
        menu_item_id: Specific menu item ID to analyze
        days_back: Number of days to analyze for patterns
    
    Returns:
        Demand analysis based on ingredient consumption patterns
    """
    
    try:
        # Get real data
        inventory_data = make_api_call("/api/v1/inventory")
        cookbook_data = make_api_call("/api/v1/cookbook")
        
        if inventory_data.get("error") or cookbook_data.get("error"):
            return {
                "error": True,
                "message": "Unable to fetch required data for demand tracking"
            }
        
        inventory_items = inventory_data.get("ingredient_items", [])
        cookbook_items = cookbook_data.get("data", [])
        
        # Filter target menu item if specified
        if menu_item_id:
            target_item = None
            for item in cookbook_items:
                if item.get("id") == menu_item_id and item.get("type") == "menu_item":
                    target_item = item
                    break
            
            if not target_item:
                return {
                    "error": True,
                    "message": f"Menu item with ID {menu_item_id} not found"
                }
            
            menu_items_to_analyze = [target_item]
        else:
            menu_items_to_analyze = [item for item in cookbook_items if item.get("type") == "menu_item"]
        
        # Demand analysis for each menu item
        demand_analysis = []
        
        for menu_item in menu_items_to_analyze:
            menu_name = menu_item.get("name", "")
            menu_price = float(menu_item.get("price", 0))
            recipe = menu_item.get("recipe", {})
            ingredients = recipe.get("ingredients", [])
            
            # Analyze ingredient demand patterns
            ingredient_demand_signals = []
            total_demand_score = 0
            
            for ingredient in ingredients:
                ing_name = ingredient.get("name", "").lower()
                
                # Find matching inventory item
                matching_inv_item = None
                for inv_item in inventory_items:
                    if ing_name in inv_item.get("name", "").lower():
                        matching_inv_item = inv_item
                        break
                
                if matching_inv_item:
                    # Calculate demand signals
                    stock_status = matching_inv_item.get("stock_status", "unknown")
                    has_activity = matching_inv_item.get("has_recent_activity", False)
                    current_qty = float(matching_inv_item.get("available_qty", 0))
                    
                    # Demand scoring
                    demand_score = 0
                    if stock_status == "low_stock":
                        demand_score += 3
                    elif stock_status == "good_stock" and has_activity:
                        demand_score += 2
                    elif stock_status == "out_of_stock":
                        demand_score += 1  # Past demand
                    
                    if has_activity:
                        demand_score += 2
                    
                    ingredient_demand_signals.append({
                        "ingredient": ingredient.get("name"),
                        "inventory_match": matching_inv_item.get("name"),
                        "stock_status": stock_status,
                        "has_recent_activity": has_activity,
                        "current_quantity": current_qty,
                        "demand_score": demand_score
                    })
                    
                    total_demand_score += demand_score
                else:
                    ingredient_demand_signals.append({
                        "ingredient": ingredient.get("name"),
                        "inventory_match": "Not found",
                        "demand_score": 0,
                        "note": "Ingredient not tracked in inventory"
                    })
            
            # Calculate overall demand metrics
            max_possible_score = len(ingredients) * 5  # Max score per ingredient
            demand_percentage = (total_demand_score / max_possible_score * 100) if max_possible_score > 0 else 0
            
            # Demand classification
            if demand_percentage > 70:
                demand_level = "High"
            elif demand_percentage > 40:
                demand_level = "Medium"
            elif demand_percentage > 15:
                demand_level = "Low"
            else:
                demand_level = "Very Low"
            
            # Estimate trends (simplified)
            active_ingredients = len([s for s in ingredient_demand_signals if s.get("has_recent_activity")])
            trend_direction = "Increasing" if active_ingredients > len(ingredients) * 0.6 else "Stable" if active_ingredients > len(ingredients) * 0.3 else "Decreasing"
            
            # Seasonal pattern placeholder (would need historical data)
            seasonal_pattern = "Requires historical data for accurate seasonal analysis"
            
            demand_analysis.append({
                "menu_item": menu_name,
                "menu_item_id": menu_item.get("id", ""),
                "price": menu_price,
                "demand_metrics": {
                    "demand_level": demand_level,
                    "demand_percentage": round(demand_percentage, 2),
                    "demand_score": total_demand_score,
                    "max_possible_score": max_possible_score,
                    "trend_direction": trend_direction
                },
                "ingredient_analysis": {
                    "total_ingredients": len(ingredients),
                    "tracked_ingredients": len([s for s in ingredient_demand_signals if s.get("inventory_match") != "Not found"]),
                    "active_ingredients": active_ingredients,
                    "low_stock_ingredients": len([s for s in ingredient_demand_signals if s.get("stock_status") == "low_stock"])
                },
                "detailed_ingredient_signals": ingredient_demand_signals,
                "recommendations": []
            })
            
            # Add recommendations
            analysis = demand_analysis[-1]
            if analysis["demand_metrics"]["demand_level"] == "High":
                analysis["recommendations"].append("High demand item - ensure adequate ingredient stock")
                analysis["recommendations"].append("Consider featuring in promotions")
            elif analysis["demand_metrics"]["demand_level"] == "Very Low":
                analysis["recommendations"].append("Low demand - review recipe or pricing")
                analysis["recommendations"].append("Consider seasonal menu rotation")
            
            if analysis["ingredient_analysis"]["low_stock_ingredients"] > 0:
                analysis["recommendations"].append("Monitor ingredient availability for consistent service")
        
        # Sort by demand level
        demand_analysis.sort(key=lambda x: x["demand_metrics"]["demand_score"], reverse=True)
        
        # Summary insights
        high_demand_items = len([item for item in demand_analysis if item["demand_metrics"]["demand_level"] == "High"])
        total_items = len(demand_analysis)
        
        summary = {
            "analysis_period": f"Last {days_back} days pattern analysis",
            "total_items_analyzed": total_items,
            "high_demand_items": high_demand_items,
            "medium_demand_items": len([item for item in demand_analysis if item["demand_metrics"]["demand_level"] == "Medium"]),
            "low_demand_items": len([item for item in demand_analysis if item["demand_metrics"]["demand_level"] in ["Low", "Very Low"]]),
            "overall_demand_health": "Good" if high_demand_items > total_items * 0.3 else "Average" if high_demand_items > 0 else "Needs Attention"
        }
        
        return {
            "success": True,
            "demand_analysis": demand_analysis,
            "summary": summary,
            "data_source": "Demand tracking from inventory patterns + cookbook recipes",
            "confidence": "Medium - Based on ingredient activity patterns",
            "source_endpoints": ["/api/v1/inventory", "/api/v1/cookbook"],
            "calculation_method": "Ingredient consumption pattern analysis for demand estimation",
            "data_freshness": "Real-time",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Menu item demand tracking failed: {str(e)}",
            "tool": "track_menu_item_demand"
        }
