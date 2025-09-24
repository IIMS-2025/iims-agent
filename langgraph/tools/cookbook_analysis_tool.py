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
