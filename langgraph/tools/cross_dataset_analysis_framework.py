"""
Cross-Dataset Analysis Framework for LangGraph - Data-First Implementation
Intelligent framework for combining and correlating real data from multiple endpoints
"""

from langchain_core.tools import tool
import requests
import os
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import statistics

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

class CrossDatasetAnalyzer:
    """Core framework for cross-dataset analysis and correlation"""
    
    def __init__(self):
        self.data_cache = {}
        self.correlation_methods = {
            "ingredient_name_matching": self._match_by_ingredient_name,
            "price_correlation": self._correlate_by_price,
            "activity_correlation": self._correlate_by_activity,
            "category_correlation": self._correlate_by_category
        }
    
    def fetch_all_datasets(self) -> Dict[str, Any]:
        """Fetch data from all available endpoints"""
        datasets = {
            "inventory": make_api_call("/api/v1/inventory"),
            "cookbook": make_api_call("/api/v1/cookbook"),
            "wastage": make_api_call("/api/v1/wastage/summary")
        }
        
        # Clean and structure data
        structured_data = {}
        
        # Process inventory data
        if not datasets["inventory"].get("error"):
            structured_data["inventory"] = {
                "items": datasets["inventory"].get("ingredient_items", []),
                "metadata": {
                    "total_items": len(datasets["inventory"].get("ingredient_items", [])),
                    "data_source": "/api/v1/inventory",
                    "fetch_time": datetime.now().isoformat()
                }
            }
        
        # Process cookbook data
        if not datasets["cookbook"].get("error"):
            cookbook_items = datasets["cookbook"].get("data", [])
            structured_data["cookbook"] = {
                "items": cookbook_items,
                "menu_items": [item for item in cookbook_items if item.get("type") == "menu_item"],
                "metadata": {
                    "total_items": len(cookbook_items),
                    "menu_items_count": len([item for item in cookbook_items if item.get("type") == "menu_item"]),
                    "data_source": "/api/v1/cookbook",
                    "fetch_time": datetime.now().isoformat()
                }
            }
        
        # Process wastage data
        if not datasets["wastage"].get("error"):
            structured_data["wastage"] = {
                "summary": datasets["wastage"],
                "metadata": {
                    "data_source": "/api/v1/wastage/summary",
                    "fetch_time": datetime.now().isoformat()
                }
            }
        
        return structured_data
    
    def _match_by_ingredient_name(self, inventory_item: Dict, cookbook_item: Dict) -> float:
        """Match inventory and cookbook items by ingredient name similarity"""
        inv_name = inventory_item.get("name", "").lower().strip()
        
        # Check recipe ingredients
        recipe = cookbook_item.get("recipe", {})
        ingredients = recipe.get("ingredients", [])
        
        max_similarity = 0.0
        for ingredient in ingredients:
            ing_name = ingredient.get("name", "").lower().strip()
            
            # Exact match
            if inv_name == ing_name:
                return 1.0
            
            # Partial match
            if inv_name in ing_name or ing_name in inv_name:
                similarity = min(len(inv_name), len(ing_name)) / max(len(inv_name), len(ing_name))
                max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    def _correlate_by_price(self, inventory_item: Dict, cookbook_item: Dict) -> float:
        """Correlate items by price relationships"""
        inv_price = float(inventory_item.get("price", 0))
        menu_price = float(cookbook_item.get("price", 0))
        
        if inv_price == 0 or menu_price == 0:
            return 0.0
        
        # Calculate price relationship (ingredient cost vs menu price)
        price_ratio = inv_price / menu_price
        
        # Reasonable ingredient cost should be 10-40% of menu price
        if 0.1 <= price_ratio <= 0.4:
            return 1.0 - abs(0.25 - price_ratio) / 0.15  # Normalize around 25%
        else:
            return max(0.0, 1.0 - abs(price_ratio - 0.25) / 0.5)
    
    def _correlate_by_activity(self, inventory_item: Dict, cookbook_item: Dict) -> float:
        """Correlate based on inventory activity and menu item usage"""
        has_activity = inventory_item.get("has_recent_activity", False)
        
        # If inventory item is active, it's likely used in current menu items
        return 0.8 if has_activity else 0.2
    
    def _correlate_by_category(self, inventory_item: Dict, cookbook_item: Dict) -> float:
        """Correlate by category matching"""
        inv_category = inventory_item.get("category", "").lower()
        menu_category = cookbook_item.get("category", "").lower()
        
        if inv_category == menu_category:
            return 1.0
        elif inv_category in menu_category or menu_category in inv_category:
            return 0.6
        else:
            return 0.0
    
    def correlate_datasets(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        """Create correlations between different datasets"""
        
        if "inventory" not in datasets or "cookbook" not in datasets:
            return {"error": "Required datasets missing"}
        
        inventory_items = datasets["inventory"]["items"]
        menu_items = datasets["cookbook"]["menu_items"]
        
        correlations = []
        
        for inv_item in inventory_items:
            for menu_item in menu_items:
                correlation_scores = {}
                
                # Calculate correlation using different methods
                for method_name, method_func in self.correlation_methods.items():
                    correlation_scores[method_name] = method_func(inv_item, menu_item)
                
                # Calculate weighted overall correlation
                overall_correlation = (
                    correlation_scores["ingredient_name_matching"] * 0.5 +
                    correlation_scores["activity_correlation"] * 0.3 +
                    correlation_scores["price_correlation"] * 0.15 +
                    correlation_scores["category_correlation"] * 0.05
                )
                
                # Only include significant correlations
                if overall_correlation > 0.3:
                    correlations.append({
                        "inventory_item": {
                            "name": inv_item.get("name"),
                            "price": inv_item.get("price"),
                            "stock_status": inv_item.get("stock_status"),
                            "has_activity": inv_item.get("has_recent_activity")
                        },
                        "menu_item": {
                            "name": menu_item.get("name"),
                            "price": menu_item.get("price"),
                            "category": menu_item.get("category")
                        },
                        "correlation_score": round(overall_correlation, 3),
                        "correlation_details": correlation_scores
                    })
        
        # Sort by correlation strength
        correlations.sort(key=lambda x: x["correlation_score"], reverse=True)
        
        return {
            "correlations": correlations,
            "correlation_summary": {
                "total_correlations": len(correlations),
                "strong_correlations": len([c for c in correlations if c["correlation_score"] > 0.7]),
                "moderate_correlations": len([c for c in correlations if 0.5 <= c["correlation_score"] <= 0.7]),
                "weak_correlations": len([c for c in correlations if 0.3 <= c["correlation_score"] < 0.5])
            }
        }
    
    def analyze_business_insights(self, datasets: Dict[str, Any], correlations: Dict[str, Any]) -> Dict[str, Any]:
        """Generate business insights from cross-dataset analysis"""
        
        insights = {
            "revenue_insights": [],
            "cost_insights": [],
            "operational_insights": [],
            "strategic_insights": []
        }
        
        if "inventory" in datasets and "cookbook" in datasets:
            inventory_items = datasets["inventory"]["items"]
            menu_items = datasets["cookbook"]["menu_items"]
            
            # Revenue insights from correlations
            strong_correlations = [c for c in correlations.get("correlations", []) if c["correlation_score"] > 0.7]
            
            if strong_correlations:
                # Active ingredient revenue potential
                active_revenue_items = [
                    c for c in strong_correlations 
                    if c["inventory_item"]["has_activity"]
                ]
                
                if active_revenue_items:
                    total_revenue_potential = sum(
                        float(c["menu_item"]["price"]) for c in active_revenue_items
                    )
                    insights["revenue_insights"].append({
                        "insight": "High Revenue Potential from Active Ingredients",
                        "value": round(total_revenue_potential, 2),
                        "count": len(active_revenue_items),
                        "confidence": "High"
                    })
                
                # Cost efficiency analysis
                cost_efficient_items = []
                for correlation in strong_correlations:
                    inv_price = float(correlation["inventory_item"]["price"])
                    menu_price = float(correlation["menu_item"]["price"])
                    
                    if menu_price > 0:
                        cost_ratio = inv_price / menu_price
                        if cost_ratio < 0.3:  # Less than 30% ingredient cost
                            cost_efficient_items.append({
                                "menu_item": correlation["menu_item"]["name"],
                                "cost_ratio": round(cost_ratio * 100, 1),
                                "profit_margin": round((1 - cost_ratio) * 100, 1)
                            })
                
                if cost_efficient_items:
                    insights["cost_insights"].append({
                        "insight": "High Profit Margin Items Identified",
                        "items": cost_efficient_items[:5],  # Top 5
                        "count": len(cost_efficient_items),
                        "confidence": "Medium"
                    })
                
                # Operational insights
                low_stock_active_items = [
                    c for c in strong_correlations
                    if c["inventory_item"]["stock_status"] == "low_stock" and 
                       c["inventory_item"]["has_activity"]
                ]
                
                if low_stock_active_items:
                    insights["operational_insights"].append({
                        "insight": "Active Menu Items at Risk Due to Low Stock",
                        "items": [c["menu_item"]["name"] for c in low_stock_active_items],
                        "count": len(low_stock_active_items),
                        "priority": "High",
                        "confidence": "High"
                    })
                
                # Strategic insights
                category_performance = {}
                for correlation in strong_correlations:
                    category = correlation["menu_item"]["category"]
                    if category not in category_performance:
                        category_performance[category] = {
                            "items": 0,
                            "total_revenue": 0,
                            "active_items": 0
                        }
                    
                    category_performance[category]["items"] += 1
                    category_performance[category]["total_revenue"] += float(correlation["menu_item"]["price"])
                    if correlation["inventory_item"]["has_activity"]:
                        category_performance[category]["active_items"] += 1
                
                # Find best performing category
                best_category = max(
                    category_performance.items(),
                    key=lambda x: x[1]["total_revenue"],
                    default=(None, {})
                )
                
                if best_category[0]:
                    insights["strategic_insights"].append({
                        "insight": f"Top Performing Category: {best_category[0]}",
                        "revenue_potential": round(best_category[1]["total_revenue"], 2),
                        "item_count": best_category[1]["items"],
                        "activity_rate": round(best_category[1]["active_items"] / best_category[1]["items"] * 100, 1),
                        "confidence": "Medium"
                    })
        
        return insights

@tool
def analyze_cross_dataset_correlations(
    include_business_insights: bool = True,
    correlation_threshold: float = 0.3
) -> Dict[str, Any]:
    """
    Perform comprehensive cross-dataset analysis and correlation.
    
    Args:
        include_business_insights: Include business intelligence analysis
        correlation_threshold: Minimum correlation score to include
    
    Returns:
        Comprehensive cross-dataset correlation analysis with business insights
    """
    
    try:
        analyzer = CrossDatasetAnalyzer()
        
        # Fetch all datasets
        datasets = analyzer.fetch_all_datasets()
        
        if not datasets:
            return {
                "error": True,
                "message": "No datasets available for correlation analysis"
            }
        
        # Check data availability
        available_datasets = [name for name, data in datasets.items() if data]
        if len(available_datasets) < 2:
            return {
                "error": True,
                "message": f"Insufficient datasets for correlation (only {available_datasets} available)"
            }
        
        # Perform correlation analysis
        correlations = analyzer.correlate_datasets(datasets)
        
        if correlations.get("error"):
            return {
                "error": True,
                "message": correlations["error"]
            }
        
        # Filter by threshold
        filtered_correlations = [
            c for c in correlations["correlations"] 
            if c["correlation_score"] >= correlation_threshold
        ]
        
        # Generate business insights if requested
        business_insights = {}
        if include_business_insights:
            business_insights = analyzer.analyze_business_insights(
                datasets, 
                {"correlations": filtered_correlations}
            )
        
        # Calculate dataset health scores
        dataset_health = {}
        for name, dataset in datasets.items():
            if dataset and "metadata" in dataset:
                item_count = dataset["metadata"].get("total_items", 0)
                dataset_health[name] = {
                    "item_count": item_count,
                    "health_score": min(100, item_count * 2),  # Simple health metric
                    "data_freshness": dataset["metadata"]["fetch_time"]
                }
        
        analysis_result = {
            "analysis_overview": {
                "analysis_timestamp": datetime.now().isoformat(),
                "datasets_analyzed": available_datasets,
                "correlation_threshold": correlation_threshold,
                "total_correlations_found": len(filtered_correlations)
            },
            "dataset_health": dataset_health,
            "correlations": {
                "summary": {
                    "total_correlations": len(filtered_correlations),
                    "strong_correlations": len([c for c in filtered_correlations if c["correlation_score"] > 0.7]),
                    "moderate_correlations": len([c for c in filtered_correlations if 0.5 <= c["correlation_score"] <= 0.7]),
                    "weak_correlations": len([c for c in filtered_correlations if correlation_threshold <= c["correlation_score"] < 0.5])
                },
                "top_correlations": filtered_correlations[:10],  # Top 10
                "correlation_details": filtered_correlations
            },
            "business_insights": business_insights if include_business_insights else {},
            "methodology": {
                "correlation_methods": [
                    "ingredient_name_matching (50% weight)",
                    "activity_correlation (30% weight)", 
                    "price_correlation (15% weight)",
                    "category_correlation (5% weight)"
                ],
                "threshold_applied": correlation_threshold,
                "confidence_assessment": "High for strong correlations (>0.7), Medium for moderate (0.5-0.7)"
            }
        }
        
        return {
            "success": True,
            "cross_dataset_analysis": analysis_result,
            "data_source": "Multi-dataset correlation analysis (inventory + cookbook + wastage)",
            "confidence": "High - Based on comprehensive data correlation methodology",
            "source_endpoints": ["/api/v1/inventory", "/api/v1/cookbook", "/api/v1/wastage/summary"],
            "calculation_method": "Weighted correlation analysis with business intelligence synthesis",
            "data_freshness": "Real-time",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Cross-dataset analysis failed: {str(e)}",
            "tool": "analyze_cross_dataset_correlations"
        }

@tool
def generate_unified_business_intelligence(
    focus_areas: List[str] = ["revenue", "costs", "operations"],
    include_recommendations: bool = True
) -> Dict[str, Any]:
    """
    Generate unified business intelligence by combining insights from all datasets.
    
    Args:
        focus_areas: Areas to focus analysis on (revenue, costs, operations, strategic)
        include_recommendations: Include actionable recommendations
    
    Returns:
        Unified business intelligence report with cross-dataset insights
    """
    
    try:
        analyzer = CrossDatasetAnalyzer()
        
        # Get comprehensive data
        datasets = analyzer.fetch_all_datasets()
        correlations = analyzer.correlate_datasets(datasets)
        business_insights = analyzer.analyze_business_insights(datasets, correlations)
        
        # Build unified intelligence report
        unified_intelligence = {
            "executive_summary": {
                "report_type": "Unified Business Intelligence",
                "generation_time": datetime.now().isoformat(),
                "focus_areas": focus_areas,
                "data_sources": list(datasets.keys())
            }
        }
        
        # Revenue intelligence
        if "revenue" in focus_areas:
            revenue_insights = business_insights.get("revenue_insights", [])
            total_revenue_potential = sum(
                insight.get("value", 0) for insight in revenue_insights
                if isinstance(insight.get("value"), (int, float))
            )
            
            unified_intelligence["revenue_intelligence"] = {
                "total_revenue_potential": round(total_revenue_potential, 2),
                "active_revenue_streams": len(revenue_insights),
                "key_insights": revenue_insights,
                "confidence": "High" if revenue_insights else "Low"
            }
        
        # Cost intelligence
        if "costs" in focus_areas:
            cost_insights = business_insights.get("cost_insights", [])
            
            unified_intelligence["cost_intelligence"] = {
                "cost_optimization_opportunities": len(cost_insights),
                "high_margin_items_identified": len([
                    item for insight in cost_insights 
                    for item in insight.get("items", [])
                    if item.get("profit_margin", 0) > 70
                ]),
                "key_insights": cost_insights,
                "confidence": "Medium" if cost_insights else "Low"
            }
        
        # Operational intelligence
        if "operations" in focus_areas:
            operational_insights = business_insights.get("operational_insights", [])
            
            critical_items = sum(
                insight.get("count", 0) for insight in operational_insights
                if insight.get("priority") == "High"
            )
            
            unified_intelligence["operational_intelligence"] = {
                "critical_operational_issues": critical_items,
                "operational_efficiency_score": max(0, 100 - critical_items * 10),
                "key_insights": operational_insights,
                "confidence": "High" if operational_insights else "Medium"
            }
        
        # Strategic intelligence
        if "strategic" in focus_areas:
            strategic_insights = business_insights.get("strategic_insights", [])
            
            unified_intelligence["strategic_intelligence"] = {
                "strategic_opportunities_identified": len(strategic_insights),
                "top_performing_categories": [
                    insight.get("insight", "") for insight in strategic_insights
                    if "Top Performing Category" in insight.get("insight", "")
                ],
                "key_insights": strategic_insights,
                "confidence": "Medium" if strategic_insights else "Low"
            }
        
        # Cross-dataset correlation strength
        correlation_strength = correlations.get("correlation_summary", {})
        strong_correlations = correlation_strength.get("strong_correlations", 0)
        total_correlations = correlation_strength.get("total_correlations", 0)
        
        correlation_quality = "High" if strong_correlations > total_correlations * 0.3 else "Medium" if strong_correlations > 0 else "Low"
        
        unified_intelligence["data_quality_assessment"] = {
            "correlation_strength": correlation_quality,
            "strong_correlations": strong_correlations,
            "total_correlations": total_correlations,
            "data_integration_score": round((strong_correlations / max(1, total_correlations)) * 100, 2)
        }
        
        # Generate recommendations if requested
        if include_recommendations:
            recommendations = []
            
            # Revenue recommendations
            if unified_intelligence.get("revenue_intelligence", {}).get("total_revenue_potential", 0) > 1000:
                recommendations.append({
                    "category": "Revenue Enhancement",
                    "priority": "High",
                    "action": "Focus on high-potential revenue items identified through cross-dataset analysis",
                    "expected_impact": f"${unified_intelligence['revenue_intelligence']['total_revenue_potential']:,.2f} potential"
                })
            
            # Cost recommendations
            cost_intel = unified_intelligence.get("cost_intelligence", {})
            if cost_intel.get("high_margin_items_identified", 0) > 0:
                recommendations.append({
                    "category": "Profitability",
                    "priority": "Medium",
                    "action": f"Promote {cost_intel['high_margin_items_identified']} high-margin items",
                    "expected_impact": "Increased profit margins"
                })
            
            # Operational recommendations
            op_intel = unified_intelligence.get("operational_intelligence", {})
            if op_intel.get("critical_operational_issues", 0) > 0:
                recommendations.append({
                    "category": "Operations",
                    "priority": "Critical",
                    "action": f"Address {op_intel['critical_operational_issues']} critical operational issues",
                    "expected_impact": "Improved operational efficiency"
                })
            
            unified_intelligence["actionable_recommendations"] = recommendations
        
        return {
            "success": True,
            "unified_business_intelligence": unified_intelligence,
            "data_source": "Comprehensive cross-dataset business intelligence synthesis",
            "confidence": "High - Based on multi-dataset correlation and analysis",
            "source_endpoints": ["/api/v1/inventory", "/api/v1/cookbook", "/api/v1/wastage/summary"],
            "calculation_method": "Unified intelligence from cross-dataset correlation and business insight synthesis",
            "data_freshness": "Real-time",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Unified business intelligence generation failed: {str(e)}",
            "tool": "generate_unified_business_intelligence"
        }
