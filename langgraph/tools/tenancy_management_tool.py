"""
Tenancy Management Tool for LangGraph
Tools for analyzing tenants, locations, and product catalogs
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
        "Content-Type": "application/json"
    }
    
    # Add tenant header only when needed
    if X_TENANT_ID and "/tenancy/" not in endpoint:
        headers["X-Tenant-ID"] = X_TENANT_ID
    
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
def get_tenant_information(
    include_locations: bool = True,
    include_products_summary: bool = True
) -> Dict[str, Any]:
    """
    Get comprehensive tenant information including locations and product overview.
    
    Args:
        include_locations: Include location details for the tenant
        include_products_summary: Include product catalog summary
    
    Returns:
        Tenant details with business insights and operational overview
    """
    
    try:
        # Get all tenants
        tenants_data = make_api_call("/api/v1/tenancy/tenants")
        
        # Check if API call returned an error (only if it's a dict)
        if isinstance(tenants_data, dict) and tenants_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to connect to backend server: {tenants_data.get('message')}",
                "endpoint": "/api/v1/tenancy/tenants",
                "suggestion": "Please ensure the inventory backend API is running on port 8000"
            }
        
        # Process tenant information - handle both list and single object cases
        if isinstance(tenants_data, list):
            tenants = tenants_data
        elif isinstance(tenants_data, dict) and not tenants_data.get("error"):
            tenants = [tenants_data]
        else:
            tenants = []
        
        tenant_analysis = []
        for tenant in tenants:
            tenant_info = {
                "id": tenant.get("id"),
                "name": tenant.get("name", "Unknown"),
                "currency": tenant.get("currency", "USD"),
                "created_at": tenant.get("created_at", ""),
                "status": tenant.get("status", "active"),
                "business_type": tenant.get("business_type", "restaurant")
            }
            
            # Add location information if requested
            if include_locations:
                locations_data = make_api_call(f"/api/v1/tenancy/locations?tenant_id={tenant.get('id')}")
                # Check if locations API returned an error (only if it's a dict)
                if not (isinstance(locations_data, dict) and locations_data.get("error")):
                    locations = locations_data if isinstance(locations_data, list) else [locations_data]
                    tenant_info["locations"] = [
                        {
                            "id": loc.get("id"),
                            "name": loc.get("name", "Unknown"),
                            "address": loc.get("address", ""),
                            "city": loc.get("city", ""),
                            "state": loc.get("state", ""),
                            "country": loc.get("country", ""),
                            "status": loc.get("status", "active")
                        }
                        for loc in locations
                    ]
                    tenant_info["location_count"] = len(locations)
                else:
                    tenant_info["locations"] = []
                    tenant_info["location_count"] = 0
            
            # Add product summary if requested
            if include_products_summary:
                products_data = make_api_call(f"/api/v1/tenancy/products?tenant_id={tenant.get('id')}")
                # Check if products API returned an error (only if it's a dict)
                if not (isinstance(products_data, dict) and products_data.get("error")):
                    products = products_data if isinstance(products_data, list) else [products_data]
                    
                    # Analyze product catalog
                    product_types = {}
                    categories = {}
                    total_value = 0
                    
                    for product in products:
                        product_type = product.get("type", "unknown")
                        category = product.get("category", "uncategorized")
                        price = float(product.get("price", 0))
                        
                        product_types[product_type] = product_types.get(product_type, 0) + 1
                        categories[category] = categories.get(category, 0) + 1
                        total_value += price
                    
                    tenant_info["product_catalog"] = {
                        "total_products": len(products),
                        "product_types": product_types,
                        "categories": categories,
                        "total_catalog_value": total_value,
                        "average_product_price": total_value / len(products) if products else 0
                    }
                else:
                    tenant_info["product_catalog"] = {
                        "total_products": 0,
                        "error": "Unable to fetch product data"
                    }
            
            tenant_analysis.append(tenant_info)
        
        return {
            "success": True,
            "tenant_information": tenant_analysis,
            "business_insights": {
                "total_tenants": len(tenant_analysis),
                "active_tenants": len([t for t in tenant_analysis if t.get("status") == "active"]),
                "total_locations": sum(t.get("location_count", 0) for t in tenant_analysis),
                "multi_location_tenants": len([t for t in tenant_analysis if t.get("location_count", 0) > 1])
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Tenant information query failed: {str(e)}",
            "tool": "get_tenant_information"
        }

@tool
def analyze_product_catalog(
    tenant_id: Optional[str] = None,
    product_type: Optional[str] = None,
    category: Optional[str] = None,
    include_pricing_analysis: bool = True
) -> Dict[str, Any]:
    """
    Analyze product catalog structure, pricing, and business insights.
    
    Args:
        tenant_id: Specific tenant to analyze (uses default if not provided)
        product_type: Filter by product type (raw_material, sub_product, menu_item)
        category: Filter by product category
        include_pricing_analysis: Include detailed pricing analysis
    
    Returns:
        Product catalog analysis with pricing insights and recommendations
    """
    
    try:
        # Build API parameters
        params = []
        if tenant_id:
            params.append(f"tenant_id={tenant_id}")
        if product_type:
            params.append(f"type={product_type}")
        if category:
            params.append(f"category={category}")
        
        query_string = "&".join(params)
        endpoint = f"/api/v1/tenancy/products?{query_string}" if params else "/api/v1/tenancy/products"
        
        products_data = make_api_call(endpoint)
        
        # Check if API call returned an error (only if it's a dict)
        if isinstance(products_data, dict) and products_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to connect to backend server: {products_data.get('message')}",
                "endpoint": endpoint,
                "suggestion": "Please ensure the inventory backend API is running on port 8000"
            }
        
        products = products_data if isinstance(products_data, list) else [products_data]
        
        # Analyze product catalog
        catalog_analysis = {
            "total_products": len(products),
            "product_types": {},
            "categories": {},
            "price_analysis": {},
            "products_by_type": {}
        }
        
        total_value = 0
        prices_by_type = {}
        
        for product in products:
            product_type = product.get("type", "unknown")
            category = product.get("category", "uncategorized")
            price = float(product.get("price", 0))
            unit = product.get("unit", "")
            
            # Count by type and category
            catalog_analysis["product_types"][product_type] = catalog_analysis["product_types"].get(product_type, 0) + 1
            catalog_analysis["categories"][category] = catalog_analysis["categories"].get(category, 0) + 1
            
            # Track products by type
            if product_type not in catalog_analysis["products_by_type"]:
                catalog_analysis["products_by_type"][product_type] = []
            
            catalog_analysis["products_by_type"][product_type].append({
                "id": product.get("id"),
                "name": product.get("name", "Unknown"),
                "category": category,
                "price": price,
                "unit": unit,
                "description": product.get("description", "")
            })
            
            # Price analysis
            if product_type not in prices_by_type:
                prices_by_type[product_type] = []
            prices_by_type[product_type].append(price)
            
            total_value += price
        
        # Pricing analysis
        if include_pricing_analysis and products:
            catalog_analysis["price_analysis"] = {
                "total_catalog_value": total_value,
                "average_price": total_value / len(products),
                "price_by_type": {},
                "pricing_insights": {}
            }
            
            for ptype, prices in prices_by_type.items():
                if prices:
                    catalog_analysis["price_analysis"]["price_by_type"][ptype] = {
                        "count": len(prices),
                        "min_price": min(prices),
                        "max_price": max(prices),
                        "average_price": sum(prices) / len(prices),
                        "total_value": sum(prices)
                    }
            
            # Pricing insights
            menu_items = [p for p in products if p.get("type") == "menu_item"]
            raw_materials = [p for p in products if p.get("type") == "raw_material"]
            
            catalog_analysis["price_analysis"]["pricing_insights"] = {
                "menu_item_count": len(menu_items),
                "raw_material_count": len(raw_materials),
                "avg_menu_price": sum(float(p.get("price", 0)) for p in menu_items) / len(menu_items) if menu_items else 0,
                "avg_raw_material_cost": sum(float(p.get("price", 0)) for p in raw_materials) / len(raw_materials) if raw_materials else 0,
                "recommendations": [
                    "Review pricing strategy for menu items vs raw material costs",
                    "Ensure adequate profit margins on menu items",
                    "Consider bundling complementary products",
                    "Analyze competitor pricing for market positioning"
                ]
            }
        
        # Business insights
        business_insights = {
            "catalog_completeness": "Complete" if len(products) > 50 else "Moderate" if len(products) > 20 else "Limited",
            "product_diversity": len(catalog_analysis["categories"]),
            "menu_vs_materials_ratio": (catalog_analysis["product_types"].get("menu_item", 0) / 
                                      catalog_analysis["product_types"].get("raw_material", 1)),
            "most_common_category": max(catalog_analysis["categories"].items(), key=lambda x: x[1])[0] if catalog_analysis["categories"] else "N/A"
        }
        
        return {
            "success": True,
            "filters_applied": {
                "tenant_id": tenant_id,
                "product_type": product_type,
                "category": category
            },
            "catalog_analysis": catalog_analysis,
            "business_insights": business_insights,
            "recommendations": [
                "Ensure balanced product mix across categories",
                "Review pricing consistency within categories",
                "Consider expanding under-represented categories",
                "Analyze profitability of each product type"
            ],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Product catalog analysis failed: {str(e)}",
            "tool": "analyze_product_catalog"
        }

@tool
def get_location_overview(
    tenant_id: Optional[str] = None,
    include_operational_metrics: bool = True
) -> Dict[str, Any]:
    """
    Get overview of all locations with operational insights.
    
    Args:
        tenant_id: Specific tenant to analyze (uses default if not provided)
        include_operational_metrics: Include operational analysis per location
    
    Returns:
        Location overview with operational insights and recommendations
    """
    
    try:
        # Get locations data
        endpoint = f"/api/v1/tenancy/locations?tenant_id={tenant_id}" if tenant_id else "/api/v1/tenancy/locations"
        locations_data = make_api_call(endpoint)
        
        # Check if API call returned an error (only if it's a dict)
        if isinstance(locations_data, dict) and locations_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to connect to backend server: {locations_data.get('message')}",
                "endpoint": endpoint,
                "suggestion": "Please ensure the inventory backend API is running on port 8000"
            }
        
        locations = locations_data if isinstance(locations_data, list) else [locations_data]
        
        # Analyze locations
        location_analysis = []
        geographical_distribution = {}
        
        for location in locations:
            location_info = {
                "id": location.get("id"),
                "name": location.get("name", "Unknown"),
                "address": location.get("address", ""),
                "city": location.get("city", ""),
                "state": location.get("state", ""),
                "country": location.get("country", ""),
                "postal_code": location.get("postal_code", ""),
                "status": location.get("status", "active"),
                "tenant_id": location.get("tenant_id")
            }
            
            # Track geographical distribution
            city = location.get("city", "Unknown")
            state = location.get("state", "Unknown")
            country = location.get("country", "Unknown")
            
            geo_key = f"{city}, {state}, {country}"
            geographical_distribution[geo_key] = geographical_distribution.get(geo_key, 0) + 1
            
            # Add operational metrics if requested
            if include_operational_metrics:
                # Note: In a real system, you'd fetch inventory, sales, and other metrics per location
                location_info["operational_metrics"] = {
                    "inventory_status": "Requires inventory analysis per location",
                    "recent_activity": "Requires transaction history analysis",
                    "performance_score": "Requires sales and operational data",
                    "recommendations": [
                        "Analyze location-specific inventory levels",
                        "Review location performance metrics",
                        "Compare locations for best practices"
                    ]
                }
            
            location_analysis.append(location_info)
        
        # Business insights
        business_insights = {
            "total_locations": len(locations),
            "active_locations": len([l for l in locations if l.get("status") == "active"]),
            "geographical_spread": len(geographical_distribution),
            "location_density": geographical_distribution,
            "expansion_opportunities": "Analyze market gaps for new locations",
            "operational_efficiency": "Compare location performance metrics"
        }
        
        return {
            "success": True,
            "filters_applied": {
                "tenant_id": tenant_id
            },
            "location_overview": location_analysis,
            "geographical_distribution": geographical_distribution,
            "business_insights": business_insights,
            "recommendations": [
                "Monitor performance across all locations",
                "Identify high and low performing locations",
                "Standardize operations across locations",
                "Consider location-specific inventory strategies"
            ],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Location overview analysis failed: {str(e)}",
            "tool": "get_location_overview"
        }
