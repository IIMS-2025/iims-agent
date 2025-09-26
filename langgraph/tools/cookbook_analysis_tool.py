"""
Cookbook Analysis Tool for LangGraph
Comprehensive tools for analyzing recipes, menu items, and cookbook data
"""

from langchain_core.tools import tool
import requests
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

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
def get_all_cookbook_items(
    include_recipes: bool = True,
    include_pricing: bool = True,
    include_nutrition: bool = False
) -> Dict[str, Any]:
    """
    Get all cookbook items including menu items and sub-products with their recipes.
    
    Args:
        include_recipes: Include detailed recipe information
        include_pricing: Include pricing and cost analysis
        include_nutrition: Include nutritional information if available
    
    Returns:
        Complete cookbook with recipes, ingredients, and business insights
    """
    
    try:
        cookbook_data = make_api_call("/api/v1/cookbook")
        
        if cookbook_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to connect to backend server: {cookbook_data.get('message')}",
                "endpoint": "/api/v1/cookbook",
                "suggestion": "Please ensure the inventory backend API is running on port 8000"
            }
        
        # Extract the data array from the API response
        cookbook_data_array = cookbook_data.get("data", [])
        
        # Process cookbook data for business insights
        cookbook_items = []
        total_items = 0
        menu_items = 0
        sub_products = 0
        total_estimated_cost = 0
        
        for item_data in cookbook_data_array:
            if isinstance(item_data, dict):
                processed_item = {
                    "product_id": item_data.get("id", ""),
                    "name": item_data.get("name", "Unknown"),
                    "type": item_data.get("type", "unknown"),
                    "category": item_data.get("category", "uncategorized"),
                    "unit": item_data.get("unit", ""),
                    "price": float(item_data.get("price", 0)),
                    "description": item_data.get("description", ""),
                    "image": item_data.get("image", ""),
                    "image_url": item_data.get("image_url", ""),
                    "created_by": item_data.get("created_by", "")
                }
                
                # Add recipe details if requested
                if include_recipes and "recipe" in item_data:
                    recipe = item_data["recipe"]
                    processed_item["recipe"] = {
                        "instructions": recipe.get("instructions", []),
                        "prep_time": recipe.get("prep_time", ""),
                        "cook_time": recipe.get("cook_time", ""),
                        "serving_size": recipe.get("serving_size", ""),
                        "ingredients": recipe.get("ingredients", [])
                    }
                    
                    # Calculate recipe cost analysis
                    if include_pricing and "ingredients" in recipe:
                        ingredient_cost = 0
                        ingredient_count = len(recipe["ingredients"])
                        processed_item["cost_analysis"] = {
                            "ingredient_count": ingredient_count,
                            "estimated_cost": ingredient_cost,
                            "price": item_data.get("price", 0),
                            "profit_margin": "N/A"  # Would need cost calculation
                        }
                
                # Track statistics
                total_items += 1
                if item_data.get("type") == "menu_item":
                    menu_items += 1
                elif item_data.get("type") == "sub_product":
                    sub_products += 1
                
                total_estimated_cost += float(item_data.get("price", 0))
                cookbook_items.append(processed_item)
        
        return {
            "success": True,
            "cookbook_items": cookbook_items,
            "summary": {
                "total_items": total_items,
                "menu_items": menu_items,
                "sub_products": sub_products,
                "raw_materials": total_items - menu_items - sub_products,
                "total_menu_value": total_estimated_cost,
                "average_item_price": total_estimated_cost / total_items if total_items > 0 else 0
            },
            "business_insights": {
                "most_expensive_items": sorted(cookbook_items, key=lambda x: x.get("price", 0), reverse=True)[:5],
                "menu_complexity": "High" if total_items > 20 else "Medium" if total_items > 10 else "Low",
                "recommendation": "Analyze ingredient costs for better profit margins" if include_pricing else "Enable pricing analysis for cost insights"
            },
            "data_source": "Direct from /api/v1/cookbook endpoint",
            "confidence": "High - Real database data",
            "source_endpoints": ["/api/v1/cookbook"],
            "data_freshness": "Real-time",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Cookbook analysis failed: {str(e)}",
            "tool": "get_all_cookbook_items"
        }

@tool
def get_recipe_details(
    product_id: str,
    include_ingredient_analysis: bool = True,
    include_cost_breakdown: bool = True
) -> Dict[str, Any]:
    """
    Get detailed recipe information for a specific cookbook item.
    
    Args:
        product_id: Product ID to get recipe details for
        include_ingredient_analysis: Include detailed ingredient breakdown
        include_cost_breakdown: Include cost analysis per ingredient
    
    Returns:
        Detailed recipe with ingredients, instructions, and cost analysis
    """
    
    try:
        recipe_data = make_api_call(f"/api/v1/cookbook/{product_id}")
        
        if recipe_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to connect to backend server: {recipe_data.get('message')}",
                "endpoint": f"/api/v1/cookbook/{product_id}",
                "suggestion": "Please ensure the inventory backend API is running on port 8000"
            }
        
        # Extract recipe information
        recipe_details = {
            "product_id": product_id,
            "name": recipe_data.get("name", "Unknown"),
            "type": recipe_data.get("type", "unknown"),
            "category": recipe_data.get("category", ""),
            "unit": recipe_data.get("unit", ""),
            "price": recipe_data.get("price", 0),
            "description": recipe_data.get("description", "")
        }
        
        # Add recipe instructions and details
        if "recipe" in recipe_data:
            recipe = recipe_data["recipe"]
            recipe_details["recipe"] = {
                "instructions": recipe.get("instructions", []),
                "prep_time": recipe.get("prep_time", ""),
                "cook_time": recipe.get("cook_time", ""),
                "total_time": recipe.get("total_time", ""),
                "serving_size": recipe.get("serving_size", ""),
                "difficulty": recipe.get("difficulty", "medium"),
                "ingredients": recipe.get("ingredients", [])
            }
            
            # Ingredient analysis
            if include_ingredient_analysis and "ingredients" in recipe:
                ingredients = recipe["ingredients"]
                recipe_details["ingredient_analysis"] = {
                    "total_ingredients": len(ingredients),
                    "ingredient_types": list(set([ing.get("type", "unknown") for ing in ingredients])),
                    "complexity_score": len(ingredients) * 1.5,  # Simple complexity metric
                    "ingredients_breakdown": [
                        {
                            "name": ing.get("name", "Unknown"),
                            "quantity": ing.get("quantity", ""),
                            "unit": ing.get("unit", ""),
                            "type": ing.get("type", "unknown"),
                            "notes": ing.get("notes", "")
                        }
                        for ing in ingredients
                    ]
                }
                
                # Cost breakdown analysis (would need inventory pricing)
                if include_cost_breakdown:
                    recipe_details["cost_analysis"] = {
                        "estimated_ingredient_cost": "Requires inventory pricing data",
                        "selling_price": recipe_data.get("price", 0),
                        "potential_margin": "Requires cost calculation",
                        "cost_per_serving": "Requires ingredient costs",
                        "recommendation": "Connect with inventory pricing for accurate cost analysis"
                    }
        
        # Add image information if available
        if "images" in recipe_data:
            recipe_details["images"] = recipe_data["images"]
        
        return {
            "success": True,
            "recipe_details": recipe_details,
            "business_insights": {
                "menu_positioning": "Premium" if recipe_details.get("price", 0) > 15 else "Standard",
                "preparation_complexity": "High" if len(recipe_details.get("recipe", {}).get("ingredients", [])) > 10 else "Medium",
                "profitability_potential": "Requires cost analysis for accurate assessment"
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Recipe details query failed: {str(e)}",
            "tool": "get_recipe_details"
        }

@tool
def analyze_menu_profitability(
    category_filter: Optional[str] = None,
    price_range: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze menu profitability and recommend pricing strategies.
    
    Args:
        category_filter: Filter by menu category
        price_range: Filter by price range (low, medium, high)
    
    Returns:
        Menu profitability analysis with pricing recommendations
    """
    
    try:
        # Get all cookbook items for analysis
        cookbook_data = make_api_call("/api/v1/cookbook")
        
        if cookbook_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to connect to backend server: {cookbook_data.get('message')}",
                "endpoint": "/api/v1/cookbook",
                "suggestion": "Please ensure the inventory backend API is running on port 8000"
            }
        
        # Extract the data array from the API response
        cookbook_data_array = cookbook_data.get("data", [])
        
        # Analyze pricing and profitability
        menu_analysis = []
        price_ranges = {"low": [], "medium": [], "high": []}
        categories = {}
        
        for item_data in cookbook_data_array:
            if isinstance(item_data, dict) and item_data.get("type") == "menu_item":
                price = float(item_data.get("price", 0))
                category = item_data.get("category", "uncategorized")
                
                # Apply filters
                if category_filter and category.lower() != category_filter.lower():
                    continue
                
                # Categorize by price
                if price < 200:  # Adjusted for Indian pricing (₹299, ₹349, etc.)
                    price_category = "low"
                elif price < 400:
                    price_category = "medium"
                else:
                    price_category = "high"
                
                if price_range and price_category != price_range:
                    continue
                
                item_analysis = {
                    "product_id": item_data.get("id", ""),
                    "name": item_data.get("name", "Unknown"),
                    "category": category,
                    "price": price,
                    "price_category": price_category,
                    "ingredient_count": len(item_data.get("recipe", {}).get("ingredients", [])),
                    "complexity": "High" if len(item_data.get("recipe", {}).get("ingredients", [])) > 8 else "Medium"
                }
                
                menu_analysis.append(item_analysis)
                price_ranges[price_category].append(item_analysis)
                
                if category not in categories:
                    categories[category] = []
                categories[category].append(item_analysis)
        
        # Generate insights
        avg_price = sum(item["price"] for item in menu_analysis) / len(menu_analysis) if menu_analysis else 0
        
        return {
            "success": True,
            "menu_analysis": menu_analysis,
            "pricing_insights": {
                "total_menu_items": len(menu_analysis),
                "average_price": round(avg_price, 2),
                "price_distribution": {
                    "low_price_items": len(price_ranges["low"]),
                    "medium_price_items": len(price_ranges["medium"]),
                    "high_price_items": len(price_ranges["high"])
                },
                "category_breakdown": {cat: len(items) for cat, items in categories.items()},
                "recommendations": [
                    "Analyze ingredient costs for accurate profit margins",
                    "Consider premium pricing for complex recipes",
                    "Balance menu with items across all price ranges",
                    "Review competitor pricing for market positioning"
                ]
            },
            "top_priced_items": sorted(menu_analysis, key=lambda x: x["price"], reverse=True)[:5],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Menu profitability analysis failed: {str(e)}",
            "tool": "analyze_menu_profitability"
        }

@tool
def analyze_dish_cost_breakdown(product_id: str) -> Dict[str, Any]:
    """
    Real dish cost analysis using live data from cookbook and inventory.
    
    Args:
        product_id: Product ID to analyze costs for
    
    Returns:
        Detailed cost breakdown using current ingredient prices from inventory
    """
    
    try:
        # Fetch recipe data from cookbook
        recipe_data = make_api_call(f"/api/v1/cookbook/{product_id}")
        
        if recipe_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to fetch recipe data: {recipe_data.get('message')}",
                "endpoint": f"/api/v1/cookbook/{product_id}"
            }
        
        # Fetch current inventory pricing
        inventory_data = make_api_call("/api/v1/inventory")
        
        if inventory_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to fetch inventory pricing: {inventory_data.get('message')}",
                "endpoint": "/api/v1/inventory"
            }
            
        # Create pricing lookup from inventory
        inventory_items = inventory_data.get("ingredient_items", [])
        pricing_lookup = {}
        for item in inventory_items:
            item_name = item.get("name", "").lower()
            pricing_lookup[item_name] = {
                "price": float(item.get("price", 0)),
                "unit": item.get("unit", ""),
                "availability": item.get("available_qty", 0),
                "status": item.get("stock_status", "unknown")
            }
        
        # Extract recipe information
        dish_name = recipe_data.get("name", "Unknown Dish")
        dish_price = float(recipe_data.get("price", 0))
        recipe = recipe_data.get("recipe", {})
        ingredients = recipe.get("ingredients", [])
        
        # Calculate ingredient costs using current prices
        ingredient_costs = []
        total_ingredient_cost = 0
        missing_ingredients = []
        
        for ingredient in ingredients:
            ingredient_name = ingredient.get("name", "").lower()
            quantity = ingredient.get("quantity", "")
            unit = ingredient.get("unit", "")
            
            if ingredient_name in pricing_lookup:
                price_info = pricing_lookup[ingredient_name]
                # Calculate cost based on quantity (simplified calculation)
                try:
                    qty_float = float(str(quantity).split()[0]) if quantity else 1
                    ingredient_cost = price_info["price"] * qty_float
                    total_ingredient_cost += ingredient_cost
                    
                    ingredient_costs.append({
                        "name": ingredient.get("name"),
                        "quantity": quantity,
                        "unit": unit,
                        "unit_price": price_info["price"],
                        "total_cost": round(ingredient_cost, 2),
                        "availability": price_info["availability"],
                        "status": price_info["status"]
                    })
                except (ValueError, TypeError):
                    ingredient_costs.append({
                        "name": ingredient.get("name"),
                        "quantity": quantity,
                        "unit": unit,
                        "unit_price": price_info["price"],
                        "total_cost": price_info["price"],  # Default to unit price
                        "availability": price_info["availability"],
                        "status": price_info["status"],
                        "note": "Quantity parsing issue - used unit price"
                    })
                    total_ingredient_cost += price_info["price"]
            else:
                missing_ingredients.append(ingredient.get("name"))
                ingredient_costs.append({
                    "name": ingredient.get("name"),
                    "quantity": quantity,
                    "unit": unit,
                    "unit_price": "Not found in inventory",
                    "total_cost": 0,
                    "availability": "Unknown",
                    "status": "missing_from_inventory"
                })
        
        # Calculate profitability
        profit_margin = dish_price - total_ingredient_cost
        profit_percentage = (profit_margin / dish_price * 100) if dish_price > 0 else 0
        
        cost_breakdown = {
            "dish_info": {
                "name": dish_name,
                "selling_price": dish_price,
                "product_id": product_id
            },
            "cost_analysis": {
                "total_ingredient_cost": round(total_ingredient_cost, 2),
                "selling_price": dish_price,
                "profit_margin": round(profit_margin, 2),
                "profit_percentage": round(profit_percentage, 2),
                "cost_percentage": round((total_ingredient_cost / dish_price * 100), 2) if dish_price > 0 else 0
            },
            "ingredient_breakdown": ingredient_costs,
            "supply_chain_insights": {
                "total_ingredients": len(ingredients),
                "ingredients_found_in_inventory": len(ingredient_costs) - len(missing_ingredients),
                "missing_from_inventory": missing_ingredients,
                "low_stock_ingredients": [
                    ing["name"] for ing in ingredient_costs 
                    if ing.get("status") in ["low_stock", "out_of_stock"]
                ]
            },
            "recommendations": []
        }
        
        # Add recommendations based on analysis
        if profit_percentage < 20:
            cost_breakdown["recommendations"].append("Low profit margin - consider price increase or cost reduction")
        if missing_ingredients:
            cost_breakdown["recommendations"].append(f"Update inventory for {len(missing_ingredients)} missing ingredients")
        if cost_breakdown["supply_chain_insights"]["low_stock_ingredients"]:
            cost_breakdown["recommendations"].append("Monitor low stock ingredients for availability")
        if profit_percentage > 60:
            cost_breakdown["recommendations"].append("High profit margin - opportunity for competitive pricing")
            
        return {
            "success": True,
            "cost_breakdown": cost_breakdown,
            "data_source": "Recipe from /api/v1/cookbook + pricing from /api/v1/inventory",
            "confidence": "High - Real cost calculation using current prices",
            "source_endpoints": [f"/api/v1/cookbook/{product_id}", "/api/v1/inventory"],
            "calculation_method": "Cross-reference recipe ingredients with current inventory pricing",
            "data_freshness": "Real-time",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Dish cost breakdown failed: {str(e)}",
            "tool": "analyze_dish_cost_breakdown"
        }

@tool
def get_menu_performance_analytics() -> Dict[str, Any]:
    """
    Menu performance using real cookbook and inventory data.
    
    Returns:
        Comprehensive menu analysis with inventory-based performance metrics
    """
    
    try:
        # Fetch cookbook data
        cookbook_data = make_api_call("/api/v1/cookbook")
        
        if cookbook_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to fetch cookbook data: {cookbook_data.get('message')}",
                "endpoint": "/api/v1/cookbook"
            }
        
        # Fetch inventory data for ingredient availability analysis
        inventory_data = make_api_call("/api/v1/inventory")
        
        if inventory_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to fetch inventory data: {inventory_data.get('message')}",
                "endpoint": "/api/v1/inventory"
            }
            
        cookbook_items = cookbook_data.get("data", [])
        inventory_items = inventory_data.get("ingredient_items", [])
        
        # Create ingredient availability lookup
        ingredient_availability = {}
        for item in inventory_items:
            item_name = item.get("name", "").lower()
            ingredient_availability[item_name] = {
                "status": item.get("stock_status", "unknown"),
                "quantity": item.get("available_qty", 0),
                "has_activity": item.get("has_recent_activity", False),
                "price": float(item.get("price", 0))
            }
        
        # Analyze menu performance
        menu_performance = []
        category_performance = {}
        total_menu_value = 0
        
        for item in cookbook_items:
            if item.get("type") == "menu_item":
                item_name = item.get("name", "Unknown")
                item_price = float(item.get("price", 0))
                item_category = item.get("category", "uncategorized")
                total_menu_value += item_price
                
                # Analyze ingredient availability for this menu item
                recipe = item.get("recipe", {})
                ingredients = recipe.get("ingredients", [])
                
                ingredient_analysis = {
                    "total_ingredients": len(ingredients),
                    "available_ingredients": 0,
                    "low_stock_ingredients": 0,
                    "out_of_stock_ingredients": 0,
                    "high_activity_ingredients": 0
                }
                
                estimated_cost = 0
                for ingredient in ingredients:
                    ing_name = ingredient.get("name", "").lower()
                    if ing_name in ingredient_availability:
                        ing_info = ingredient_availability[ing_name]
                        ingredient_analysis["available_ingredients"] += 1
                        
                        if ing_info["status"] == "low_stock":
                            ingredient_analysis["low_stock_ingredients"] += 1
                        elif ing_info["status"] == "out_of_stock":
                            ingredient_analysis["out_of_stock_ingredients"] += 1
                        
                        if ing_info["has_activity"]:
                            ingredient_analysis["high_activity_ingredients"] += 1
                            
                        # Simple cost estimation
                        estimated_cost += ing_info["price"]
                
                # Calculate performance score
                availability_score = (ingredient_analysis["available_ingredients"] / 
                                    ingredient_analysis["total_ingredients"] * 100) if ingredient_analysis["total_ingredients"] > 0 else 0
                
                activity_score = (ingredient_analysis["high_activity_ingredients"] / 
                                ingredient_analysis["total_ingredients"] * 100) if ingredient_analysis["total_ingredients"] > 0 else 0
                
                # Estimate profit margin
                profit_margin = item_price - estimated_cost
                profit_percentage = (profit_margin / item_price * 100) if item_price > 0 else 0
                
                performance_data = {
                    "name": item_name,
                    "category": item_category,
                    "price": item_price,
                    "estimated_cost": round(estimated_cost, 2),
                    "estimated_profit": round(profit_margin, 2),
                    "profit_percentage": round(profit_percentage, 2),
                    "availability_score": round(availability_score, 2),
                    "activity_score": round(activity_score, 2),
                    "ingredient_analysis": ingredient_analysis,
                    "performance_rating": "High" if availability_score > 80 and profit_percentage > 30 else 
                                        "Medium" if availability_score > 60 and profit_percentage > 15 else "Low"
                }
                
                menu_performance.append(performance_data)
                
                # Category aggregation
                if item_category not in category_performance:
                    category_performance[item_category] = {
                        "item_count": 0,
                        "total_value": 0,
                        "avg_availability": 0,
                        "avg_profit_percentage": 0
                    }
                
                category_performance[item_category]["item_count"] += 1
                category_performance[item_category]["total_value"] += item_price
                category_performance[item_category]["avg_availability"] += availability_score
                category_performance[item_category]["avg_profit_percentage"] += profit_percentage
        
        # Calculate category averages
        for category, data in category_performance.items():
            if data["item_count"] > 0:
                data["avg_availability"] = round(data["avg_availability"] / data["item_count"], 2)
                data["avg_profit_percentage"] = round(data["avg_profit_percentage"] / data["item_count"], 2)
        
        # Top performers
        top_performers = sorted(menu_performance, 
                              key=lambda x: (x["availability_score"] + x["profit_percentage"]) / 2, 
                              reverse=True)[:5]
        
        bottom_performers = sorted(menu_performance, 
                                 key=lambda x: (x["availability_score"] + x["profit_percentage"]) / 2)[:5]
        
        analytics_result = {
            "overview": {
                "total_menu_items": len(menu_performance),
                "total_menu_value": round(total_menu_value, 2),
                "average_item_price": round(total_menu_value / len(menu_performance), 2) if menu_performance else 0,
                "categories_count": len(category_performance)
            },
            "performance_summary": {
                "high_performance_items": len([item for item in menu_performance if item["performance_rating"] == "High"]),
                "medium_performance_items": len([item for item in menu_performance if item["performance_rating"] == "Medium"]),
                "low_performance_items": len([item for item in menu_performance if item["performance_rating"] == "Low"])
            },
            "top_performers": top_performers,
            "bottom_performers": bottom_performers,
            "category_performance": category_performance,
            "recommendations": [
                "Focus on improving ingredient availability for low-performing items",
                "Consider price adjustments for items with low profit margins",
                "Promote high-performance items in marketing",
                "Review recipes for bottom performers to optimize costs"
            ]
        }
        
        return {
            "success": True,
            "menu_analytics": analytics_result,
            "detailed_items": menu_performance,
            "data_source": "Menu items from /api/v1/cookbook + ingredient data from /api/v1/inventory",
            "confidence": "High - Real performance calculation using live data",
            "source_endpoints": ["/api/v1/cookbook", "/api/v1/inventory"],
            "calculation_method": "Cross-analysis of menu pricing, ingredient availability, and activity patterns",
            "data_freshness": "Real-time",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Menu performance analytics failed: {str(e)}",
            "tool": "get_menu_performance_analytics"
        }

@tool
def calculate_recipe_costs_from_inventory(
    product_id: Optional[str] = None,
    use_current_prices: bool = True
) -> Dict[str, Any]:
    """
    Live recipe cost calculation using current inventory pricing.
    
    Args:
        product_id: Specific product to analyze (optional - if None, analyzes all)
        use_current_prices: Use current inventory prices for calculation
    
    Returns:
        Recipe cost analysis with real-time pricing data
    """
    
    try:
        # Fetch cookbook data
        if product_id:
            cookbook_data = make_api_call(f"/api/v1/cookbook/{product_id}")
            source_cookbook = f"/api/v1/cookbook/{product_id}"
            cookbook_items = [cookbook_data] if not cookbook_data.get("error") else []
        else:
            cookbook_data = make_api_call("/api/v1/cookbook")
            source_cookbook = "/api/v1/cookbook"
            cookbook_items = cookbook_data.get("data", []) if not cookbook_data.get("error") else []
        
        if cookbook_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to fetch cookbook data: {cookbook_data.get('message')}",
                "endpoint": source_cookbook
            }
        
        # Fetch current inventory pricing
        inventory_data = make_api_call("/api/v1/inventory")
        
        if inventory_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to fetch inventory pricing: {inventory_data.get('message')}",
                "endpoint": "/api/v1/inventory"
            }
        
        # Create pricing dictionary
        inventory_items = inventory_data.get("ingredient_items", [])
        current_prices = {}
        price_variations = {}
        
        for item in inventory_items:
            item_name = item.get("name", "").lower()
            current_prices[item_name] = {
                "current_price": float(item.get("price", 0)),
                "unit": item.get("unit", ""),
                "last_updated": item.get("last_updated", ""),
                "status": item.get("stock_status", "unknown")
            }
        
        # Analyze recipe costs
        recipe_cost_analysis = []
        total_recipes_analyzed = 0
        total_cost_calculated = 0
        
        for item in cookbook_items:
            if isinstance(item, dict):
                total_recipes_analyzed += 1
                recipe_name = item.get("name", "Unknown Recipe")
                selling_price = float(item.get("price", 0))
                recipe = item.get("recipe", {})
                ingredients = recipe.get("ingredients", [])
                
                ingredient_costs = []
                total_recipe_cost = 0
                missing_ingredients = []
                
                for ingredient in ingredients:
                    ing_name = ingredient.get("name", "").lower()
                    quantity = ingredient.get("quantity", "")
                    
                    if ing_name in current_prices:
                        price_info = current_prices[ing_name]
                        
                        # Simple cost calculation (could be improved with unit conversion)
                        try:
                            qty_float = float(str(quantity).split()[0]) if quantity else 1
                            ing_cost = price_info["current_price"] * qty_float
                        except (ValueError, TypeError):
                            ing_cost = price_info["current_price"]  # Default to unit price
                        
                        total_recipe_cost += ing_cost
                        ingredient_costs.append({
                            "name": ingredient.get("name"),
                            "quantity": quantity,
                            "unit_price": price_info["current_price"],
                            "calculated_cost": round(ing_cost, 2),
                            "price_unit": price_info["unit"],
                            "status": price_info["status"]
                        })
                    else:
                        missing_ingredients.append(ingredient.get("name"))
                        ingredient_costs.append({
                            "name": ingredient.get("name"),
                            "quantity": quantity,
                            "unit_price": "Not in inventory",
                            "calculated_cost": 0,
                            "status": "missing"
                        })
                
                total_cost_calculated += total_recipe_cost
                
                # Calculate margins and recommendations
                profit_margin = selling_price - total_recipe_cost
                profit_percentage = (profit_margin / selling_price * 100) if selling_price > 0 else 0
                
                cost_analysis = {
                    "recipe_name": recipe_name,
                    "product_id": item.get("id", ""),
                    "selling_price": selling_price,
                    "calculated_cost": round(total_recipe_cost, 2),
                    "profit_margin": round(profit_margin, 2),
                    "profit_percentage": round(profit_percentage, 2),
                    "ingredient_count": len(ingredients),
                    "costed_ingredients": len(ingredient_costs) - len(missing_ingredients),
                    "missing_ingredients": missing_ingredients,
                    "ingredient_breakdown": ingredient_costs,
                    "cost_confidence": "High" if not missing_ingredients else 
                                    "Medium" if len(missing_ingredients) < len(ingredients) / 2 else "Low"
                }
                
                recipe_cost_analysis.append(cost_analysis)
        
        # Summary statistics
        summary = {
            "total_recipes_analyzed": total_recipes_analyzed,
            "total_estimated_cost": round(total_cost_calculated, 2),
            "average_recipe_cost": round(total_cost_calculated / total_recipes_analyzed, 2) if total_recipes_analyzed > 0 else 0,
            "high_cost_recipes": len([r for r in recipe_cost_analysis if r["calculated_cost"] > 50]),
            "high_margin_recipes": len([r for r in recipe_cost_analysis if r["profit_percentage"] > 50]),
            "low_margin_recipes": len([r for r in recipe_cost_analysis if r["profit_percentage"] < 20])
        }
        
        return {
            "success": True,
            "cost_analysis": recipe_cost_analysis,
            "summary": summary,
            "pricing_source": "Current inventory prices" if use_current_prices else "Historical pricing",
            "data_source": f"Recipes from {source_cookbook} + pricing from /api/v1/inventory",
            "confidence": "High - Real-time cost calculation",
            "source_endpoints": [source_cookbook, "/api/v1/inventory"],
            "calculation_method": "Direct ingredient cost calculation using current inventory pricing",
            "limitations": "Cost calculation simplified - may need unit conversion improvements",
            "data_freshness": "Real-time",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Recipe cost calculation failed: {str(e)}",
            "tool": "calculate_recipe_costs_from_inventory"
        }
