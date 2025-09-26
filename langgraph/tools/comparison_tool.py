"""
Comparison Tool for LangGraph - Data-First Implementation
Intelligent comparisons using real data from inventory, cookbook, sales, and operational metrics
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
def compare_inventory_performance(
    comparison_type: str = "status_distribution",
    include_value_analysis: bool = True,
    include_recommendations: bool = True
) -> Dict[str, Any]:
    """
    Compare current inventory performance against optimal benchmarks using real data.
    
    Args:
        comparison_type: Type of comparison (status_distribution, value_efficiency, activity_levels)
        include_value_analysis: Include monetary value comparisons
        include_recommendations: Include improvement recommendations
    
    Returns:
        Comprehensive inventory performance comparison with real data insights
    """
    
    try:
        inventory_data = make_api_call("/api/v1/inventory")
        
        if inventory_data.get("error"):
            return {
                "error": True,
                "message": "Unable to fetch inventory data for comparison"
            }
        
        inventory_items = inventory_data.get("ingredient_items", [])
        
        # Current state analysis
        current_metrics = {
            "total_items": len(inventory_items),
            "good_stock_items": len([item for item in inventory_items if item.get("stock_status") == "good_stock"]),
            "low_stock_items": len([item for item in inventory_items if item.get("stock_status") == "low_stock"]),
            "out_of_stock_items": len([item for item in inventory_items if item.get("stock_status") == "out_of_stock"]),
            "active_items": len([item for item in inventory_items if item.get("has_recent_activity")]),
            "total_value": sum(
                float(item.get("price", 0)) * float(item.get("available_qty", 0))
                for item in inventory_items
            )
        }
        
        # Industry benchmark targets (realistic targets for restaurant inventory)
        benchmark_targets = {
            "good_stock_percentage": 85.0,  # 85% should be in good stock
            "low_stock_percentage": 12.0,   # 12% acceptable in low stock
            "out_of_stock_percentage": 3.0, # 3% max out of stock
            "activity_percentage": 70.0,    # 70% should show recent activity
            "value_efficiency_score": 80.0  # Target efficiency score
        }
        
        # Calculate current percentages
        current_percentages = {
            "good_stock_percentage": (current_metrics["good_stock_items"] / current_metrics["total_items"] * 100) if current_metrics["total_items"] > 0 else 0,
            "low_stock_percentage": (current_metrics["low_stock_items"] / current_metrics["total_items"] * 100) if current_metrics["total_items"] > 0 else 0,
            "out_of_stock_percentage": (current_metrics["out_of_stock_items"] / current_metrics["total_items"] * 100) if current_metrics["total_items"] > 0 else 0,
            "activity_percentage": (current_metrics["active_items"] / current_metrics["total_items"] * 100) if current_metrics["total_items"] > 0 else 0
        }
        
        # Performance comparison
        performance_comparison = {}
        
        for metric, current_value in current_percentages.items():
            target_value = benchmark_targets.get(metric, 0)
            variance = current_value - target_value
            variance_percentage = (variance / target_value * 100) if target_value > 0 else 0
            
            performance_comparison[metric] = {
                "current": round(current_value, 2),
                "target": target_value,
                "variance": round(variance, 2),
                "variance_percentage": round(variance_percentage, 2),
                "status": "Above Target" if variance > 0 else "Below Target" if variance < -5 else "On Target"
            }
        
        # Overall performance score
        overall_score = 0
        for metric in ["good_stock_percentage", "activity_percentage"]:
            if metric in performance_comparison:
                # Positive metrics (higher is better)
                score_contribution = min(100, (current_percentages[metric] / benchmark_targets[metric] * 100))
                overall_score += score_contribution
        
        # Negative metrics (lower is better)
        for metric in ["out_of_stock_percentage"]:
            if metric in performance_comparison:
                if current_percentages[metric] <= benchmark_targets[metric]:
                    score_contribution = 100
                else:
                    score_contribution = max(0, 100 - (current_percentages[metric] - benchmark_targets[metric]) * 10)
                overall_score += score_contribution
        
        overall_score = round(overall_score / 3, 2)  # Average across 3 key metrics
        
        # Value analysis if requested
        value_analysis = {}
        if include_value_analysis:
            avg_item_value = current_metrics["total_value"] / current_metrics["total_items"] if current_metrics["total_items"] > 0 else 0
            
            # High-value items analysis
            high_value_items = [
                item for item in inventory_items 
                if float(item.get("price", 0)) * float(item.get("available_qty", 0)) > avg_item_value * 2
            ]
            
            value_analysis = {
                "total_inventory_value": round(current_metrics["total_value"], 2),
                "average_item_value": round(avg_item_value, 2),
                "high_value_items_count": len(high_value_items),
                "high_value_items_percentage": round(len(high_value_items) / current_metrics["total_items"] * 100, 2) if current_metrics["total_items"] > 0 else 0,
                "value_concentration": "High" if len(high_value_items) > current_metrics["total_items"] * 0.2 else "Moderate" if len(high_value_items) > current_metrics["total_items"] * 0.1 else "Low"
            }
        
        # Recommendations if requested
        recommendations = []
        if include_recommendations:
            if performance_comparison["good_stock_percentage"]["status"] == "Below Target":
                recommendations.append({
                    "priority": "High",
                    "category": "Stock Management",
                    "action": f"Improve stock levels - currently {current_percentages['good_stock_percentage']:.1f}% vs target {benchmark_targets['good_stock_percentage']}%",
                    "impact": "Reduces stockouts and improves service level"
                })
            
            if performance_comparison["out_of_stock_percentage"]["status"] == "Above Target":
                recommendations.append({
                    "priority": "Critical",
                    "category": "Procurement",
                    "action": f"Address {current_metrics['out_of_stock_items']} out-of-stock items immediately",
                    "impact": "Prevents menu disruption and lost sales"
                })
            
            if performance_comparison["activity_percentage"]["status"] == "Below Target":
                recommendations.append({
                    "priority": "Medium",
                    "category": "Menu Optimization",
                    "action": f"Review {current_metrics['total_items'] - current_metrics['active_items']} inactive inventory items",
                    "impact": "Improves inventory turnover and reduces waste"
                })
            
            if overall_score < 75:
                recommendations.append({
                    "priority": "High",
                    "category": "System Improvement",
                    "action": "Implement comprehensive inventory management review",
                    "impact": "Overall performance improvement across all metrics"
                })
        
        comparison_result = {
            "comparison_overview": {
                "comparison_type": comparison_type,
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                "overall_performance_score": overall_score,
                "performance_rating": "Excellent" if overall_score >= 90 else "Good" if overall_score >= 75 else "Needs Improvement",
                "total_items_analyzed": current_metrics["total_items"]
            },
            "current_state": current_metrics,
            "benchmark_comparison": performance_comparison,
            "value_analysis": value_analysis if include_value_analysis else {},
            "improvement_opportunities": recommendations if include_recommendations else [],
            "key_insights": [
                f"Overall performance score: {overall_score}/100",
                f"Stock health: {current_percentages['good_stock_percentage']:.1f}% items in good stock",
                f"Activity level: {current_percentages['activity_percentage']:.1f}% items showing activity",
                f"Critical items: {current_metrics['out_of_stock_items']} out of stock"
            ]
        }
        
        return {
            "success": True,
            "inventory_comparison": comparison_result,
            "data_source": "Real inventory performance vs industry benchmarks",
            "confidence": "High - Based on actual inventory data and industry standards",
            "source_endpoints": ["/api/v1/inventory"],
            "calculation_method": "Performance benchmarking against optimal inventory targets",
            "data_freshness": "Real-time",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Inventory comparison failed: {str(e)}",
            "tool": "compare_inventory_performance"
        }

@tool
def compare_menu_items(
    comparison_metrics: List[str] = ["price", "performance", "cost_efficiency"],
    top_n: int = 10,
    include_recommendations: bool = True
) -> Dict[str, Any]:
    """
    Compare menu items across multiple performance metrics using real data.
    
    Args:
        comparison_metrics: Metrics to compare (price, performance, cost_efficiency, popularity)
        top_n: Number of top/bottom items to highlight in each category
        include_recommendations: Include actionable recommendations
    
    Returns:
        Comprehensive menu item comparison analysis
    """
    
    try:
        inventory_data = make_api_call("/api/v1/inventory")
        cookbook_data = make_api_call("/api/v1/cookbook")
        
        if inventory_data.get("error") or cookbook_data.get("error"):
            return {
                "error": True,
                "message": "Unable to fetch required data for menu comparison"
            }
        
        inventory_items = inventory_data.get("ingredient_items", [])
        cookbook_items = cookbook_data.get("data", [])
        menu_items = [item for item in cookbook_items if item.get("type") == "menu_item"]
        
        # Create ingredient lookup for cost analysis
        ingredient_lookup = {}
        for inv_item in inventory_items:
            ingredient_lookup[inv_item.get("name", "").lower()] = {
                "price": float(inv_item.get("price", 0)),
                "has_activity": inv_item.get("has_recent_activity", False),
                "stock_status": inv_item.get("stock_status", "unknown")
            }
        
        # Analyze each menu item
        menu_analysis = []
        
        for menu_item in menu_items:
            menu_name = menu_item.get("name", "")
            menu_price = float(menu_item.get("price", 0))
            menu_category = menu_item.get("category", "uncategorized")
            recipe = menu_item.get("recipe", {})
            ingredients = recipe.get("ingredients", [])
            
            # Calculate cost efficiency
            ingredient_cost = 0
            active_ingredients = 0
            available_ingredients = 0
            
            for ingredient in ingredients:
                ing_name = ingredient.get("name", "").lower()
                if ing_name in ingredient_lookup:
                    ingredient_cost += ingredient_lookup[ing_name]["price"]
                    if ingredient_lookup[ing_name]["has_activity"]:
                        active_ingredients += 1
                    if ingredient_lookup[ing_name]["stock_status"] in ["good_stock", "low_stock"]:
                        available_ingredients += 1
            
            # Performance metrics
            profit_margin = menu_price - ingredient_cost
            profit_percentage = (profit_margin / menu_price * 100) if menu_price > 0 else 0
            performance_score = (active_ingredients / len(ingredients) * 100) if ingredients else 0
            availability_score = (available_ingredients / len(ingredients) * 100) if ingredients else 0
            
            # Overall efficiency score
            efficiency_score = (
                (profit_percentage * 0.4) +
                (performance_score * 0.3) +
                (availability_score * 0.3)
            )
            
            menu_analysis.append({
                "name": menu_name,
                "category": menu_category,
                "price": menu_price,
                "ingredient_cost": round(ingredient_cost, 2),
                "profit_margin": round(profit_margin, 2),
                "profit_percentage": round(profit_percentage, 2),
                "performance_score": round(performance_score, 2),
                "availability_score": round(availability_score, 2),
                "efficiency_score": round(efficiency_score, 2),
                "total_ingredients": len(ingredients),
                "active_ingredients": active_ingredients
            })
        
        # Comparison analysis by metrics
        comparison_results = {}
        
        if "price" in comparison_metrics:
            # Price comparison
            sorted_by_price = sorted(menu_analysis, key=lambda x: x["price"], reverse=True)
            comparison_results["price_analysis"] = {
                "highest_priced": sorted_by_price[:top_n],
                "lowest_priced": sorted_by_price[-top_n:],
                "average_price": round(sum(item["price"] for item in menu_analysis) / len(menu_analysis), 2) if menu_analysis else 0,
                "price_range": {
                    "min": min(item["price"] for item in menu_analysis) if menu_analysis else 0,
                    "max": max(item["price"] for item in menu_analysis) if menu_analysis else 0
                }
            }
        
        if "performance" in comparison_metrics:
            # Performance comparison
            sorted_by_performance = sorted(menu_analysis, key=lambda x: x["performance_score"], reverse=True)
            comparison_results["performance_analysis"] = {
                "top_performers": sorted_by_performance[:top_n],
                "low_performers": sorted_by_performance[-top_n:],
                "average_performance": round(sum(item["performance_score"] for item in menu_analysis) / len(menu_analysis), 2) if menu_analysis else 0
            }
        
        if "cost_efficiency" in comparison_metrics:
            # Cost efficiency comparison
            sorted_by_efficiency = sorted(menu_analysis, key=lambda x: x["efficiency_score"], reverse=True)
            comparison_results["efficiency_analysis"] = {
                "most_efficient": sorted_by_efficiency[:top_n],
                "least_efficient": sorted_by_efficiency[-top_n:],
                "average_efficiency": round(sum(item["efficiency_score"] for item in menu_analysis) / len(menu_analysis), 2) if menu_analysis else 0
            }
        
        # Category comparison
        category_comparison = {}
        for item in menu_analysis:
            category = item["category"]
            if category not in category_comparison:
                category_comparison[category] = {
                    "items": [],
                    "avg_price": 0,
                    "avg_efficiency": 0,
                    "avg_performance": 0
                }
            category_comparison[category]["items"].append(item)
        
        # Calculate category averages
        for category, data in category_comparison.items():
            items = data["items"]
            data["avg_price"] = round(sum(item["price"] for item in items) / len(items), 2)
            data["avg_efficiency"] = round(sum(item["efficiency_score"] for item in items) / len(items), 2)
            data["avg_performance"] = round(sum(item["performance_score"] for item in items) / len(items), 2)
            data["item_count"] = len(items)
        
        # Recommendations
        recommendations = []
        if include_recommendations:
            # High efficiency, low price items (good value)
            good_value_items = [
                item for item in menu_analysis 
                if item["efficiency_score"] > 60 and item["price"] < comparison_results.get("price_analysis", {}).get("average_price", 200)
            ]
            
            if good_value_items:
                recommendations.append({
                    "category": "Menu Promotion",
                    "priority": "Medium",
                    "action": f"Promote {len(good_value_items)} high-efficiency, affordable items",
                    "impact": "Increases profitability while maintaining customer value"
                })
            
            # Low efficiency items
            low_efficiency_items = [item for item in menu_analysis if item["efficiency_score"] < 30]
            if low_efficiency_items:
                recommendations.append({
                    "category": "Menu Optimization",
                    "priority": "High",
                    "action": f"Review {len(low_efficiency_items)} low-efficiency menu items",
                    "impact": "Improves overall menu profitability"
                })
            
            # High-margin items
            high_margin_items = [item for item in menu_analysis if item["profit_percentage"] > 70]
            if high_margin_items:
                recommendations.append({
                    "category": "Revenue Enhancement",
                    "priority": "Medium",
                    "action": f"Feature {len(high_margin_items)} high-margin items prominently",
                    "impact": "Maximizes profit per sale"
                })
        
        return {
            "success": True,
            "menu_comparison": {
                "comparison_overview": {
                    "total_items_compared": len(menu_analysis),
                    "comparison_metrics": comparison_metrics,
                    "analysis_date": datetime.now().strftime("%Y-%m-%d")
                },
                "metric_comparisons": comparison_results,
                "category_comparison": category_comparison,
                "recommendations": recommendations if include_recommendations else []
            },
            "data_source": "Menu comparison using cookbook + inventory cost analysis",
            "confidence": "High - Based on real menu and ingredient data",
            "source_endpoints": ["/api/v1/inventory", "/api/v1/cookbook"],
            "calculation_method": "Multi-metric menu performance comparison with cost analysis",
            "data_freshness": "Real-time",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Menu comparison failed: {str(e)}",
            "tool": "compare_menu_items"
        }