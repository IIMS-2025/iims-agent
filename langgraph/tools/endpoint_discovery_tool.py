"""
Endpoint Discovery Tool for LangGraph - Data-First Implementation
Intelligent endpoint discovery and verification system for ReAct pattern
"""

from langchain_core.tools import tool
import requests
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
X_TENANT_ID = os.getenv("X_TENANT_ID", "11111111-1111-1111-1111-111111111111")
X_LOCATION_ID = os.getenv("X_LOCATION_ID", "22222222-2222-2222-2222-222222222222")

def make_api_call(endpoint: str, method: str = "GET", data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
    """Helper function to make API calls with proper headers"""
    url = f"{BASE_URL}{endpoint}"
    default_headers = {
        "X-Tenant-ID": X_TENANT_ID,
        "Content-Type": "application/json"
    }
    
    if headers:
        default_headers.update(headers)
    
    # Add location header for wastage endpoints
    if "/wastage" in endpoint:
        default_headers["X-Location-ID"] = X_LOCATION_ID
    
    try:
        if method == "GET":
            response = requests.get(url, headers=default_headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=default_headers, json=data, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        return {
            "success": True,
            "status_code": response.status_code,
            "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "headers": dict(response.headers)
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": True,
            "message": f"API call failed: {str(e)}",
            "endpoint": endpoint
        }

@tool
def discover_available_endpoints(
    check_undocumented: bool = True,
    include_health_check: bool = True
) -> Dict[str, Any]:
    """
    Discover and verify available API endpoints for the ReAct pattern implementation.
    
    Args:
        check_undocumented: Check for potentially undocumented endpoints
        include_health_check: Include system health verification
    
    Returns:
        Comprehensive endpoint discovery report with availability status
    """
    
    try:
        # Known documented endpoints from IIMS_API_GET_ENDPOINTS.md
        documented_endpoints = [
            "/api/v1/healthz",
            "/api/v1/inventory",
            "/api/v1/inventory/{product_id}",
            "/api/v1/cookbook",
            "/api/v1/cookbook/{product_id}",
            "/api/v1/wastage/summary",
            "/api/v1/wastage",
            "/api/v1/wastage/by-inventory/{inventory_id}",
            "/api/v1/stock/inventory/{product_id}",
            "/api/v1/stock/batch/{batch_id}/history"
        ]
        
        # Potential undocumented endpoints (based on strategy document requirements)
        undocumented_candidates = [
            "/api/v1/sales",
            "/api/v1/sales/total-sales",
            "/api/v1/sales/{date}",
            "/api/v1/sales-analytics",
            "/api/v1/sales-analytics/top-categories",
            "/api/v1/sales-analytics/categories-summary",
            "/api/v1/orders",
            "/api/v1/analytics",
            "/api/v1/reports",
            "/api/v1/dashboard"
        ]
        
        endpoint_status = {}
        
        # Test documented endpoints
        print("Testing documented endpoints...")
        for endpoint in documented_endpoints:
            # Skip parameterized endpoints for basic discovery
            if "{" in endpoint:
                # Try with sample IDs
                test_endpoint = endpoint.replace("{product_id}", "sample").replace("{inventory_id}", "sample").replace("{batch_id}", "sample")
            else:
                test_endpoint = endpoint
            
            result = make_api_call(test_endpoint)
            endpoint_status[endpoint] = {
                "category": "documented",
                "available": result.get("success", False),
                "status_code": result.get("status_code"),
                "test_endpoint": test_endpoint,
                "response_type": "json" if result.get("success") and isinstance(result.get("data"), dict) else "other",
                "error_message": result.get("message") if not result.get("success") else None
            }
        
        # Test undocumented candidates if requested
        if check_undocumented:
            print("Testing potential undocumented endpoints...")
            for endpoint in undocumented_candidates:
                result = make_api_call(endpoint)
                endpoint_status[endpoint] = {
                    "category": "undocumented_candidate",
                    "available": result.get("success", False),
                    "status_code": result.get("status_code"),
                    "test_endpoint": endpoint,
                    "response_type": "json" if result.get("success") and isinstance(result.get("data"), dict) else "other",
                    "error_message": result.get("message") if not result.get("success") else None
                }
        
        # System health check
        health_status = {}
        if include_health_check:
            health_result = make_api_call("/api/v1/healthz")
            health_status = {
                "backend_healthy": health_result.get("success", False),
                "health_response": health_result.get("data") if health_result.get("success") else None,
                "health_check_time": datetime.now().isoformat()
            }
        
        # Analyze results
        available_endpoints = [ep for ep, status in endpoint_status.items() if status["available"]]
        missing_endpoints = [ep for ep, status in endpoint_status.items() if not status["available"]]
        
        # Categorize by functionality
        functionality_coverage = {
            "inventory_management": [ep for ep in available_endpoints if "/inventory" in ep],
            "cookbook_management": [ep for ep in available_endpoints if "/cookbook" in ep],
            "wastage_tracking": [ep for ep in available_endpoints if "/wastage" in ep],
            "stock_management": [ep for ep in available_endpoints if "/stock" in ep],
            "sales_analytics": [ep for ep in available_endpoints if "/sales" in ep],
            "system_health": [ep for ep in available_endpoints if "/healthz" in ep]
        }
        
        # Generate recommendations
        recommendations = []
        
        if not functionality_coverage["sales_analytics"]:
            recommendations.append({
                "priority": "High",
                "category": "Missing Functionality",
                "issue": "No sales analytics endpoints discovered",
                "recommendation": "Implement cross-dataset analysis using inventory + cookbook data",
                "implementation_status": "Completed via sales_analytics_tool.py"
            })
        
        if len(available_endpoints) < len(documented_endpoints) * 0.8:
            recommendations.append({
                "priority": "Medium",
                "category": "Endpoint Availability",
                "issue": f"Only {len(available_endpoints)}/{len(documented_endpoints)} documented endpoints available",
                "recommendation": "Verify backend configuration and endpoint implementation"
            })
        
        # Coverage assessment
        coverage_assessment = {
            "total_endpoints_tested": len(endpoint_status),
            "available_endpoints": len(available_endpoints),
            "missing_endpoints": len(missing_endpoints),
            "availability_percentage": round(len(available_endpoints) / len(endpoint_status) * 100, 2),
            "core_functionality_covered": len([cat for cat, eps in functionality_coverage.items() if eps]) > 3
        }
        
        discovery_result = {
            "discovery_overview": {
                "discovery_timestamp": datetime.now().isoformat(),
                "base_url": BASE_URL,
                "discovery_scope": "documented + undocumented candidates" if check_undocumented else "documented only",
                "health_check_included": include_health_check
            },
            "endpoint_status": endpoint_status,
            "health_status": health_status,
            "coverage_assessment": coverage_assessment,
            "functionality_coverage": functionality_coverage,
            "recommendations": recommendations,
            "react_pattern_readiness": {
                "tier_1_ready": len(functionality_coverage["inventory_management"]) > 0 and len(functionality_coverage["cookbook_management"]) > 0,
                "tier_2_ready": len(available_endpoints) >= 3,
                "tier_3_fallback": True,  # Always available via error handling
                "overall_readiness": "Ready" if len(available_endpoints) >= 3 else "Limited"
            }
        }
        
        return {
            "success": True,
            "endpoint_discovery": discovery_result,
            "data_source": "Direct endpoint verification and availability testing",
            "confidence": "High - Based on actual API responses",
            "source_endpoints": ["System-wide endpoint discovery"],
            "calculation_method": "Direct HTTP endpoint testing and response analysis",
            "data_freshness": "Real-time",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Endpoint discovery failed: {str(e)}",
            "tool": "discover_available_endpoints"
        }

@tool
def verify_endpoint_data_quality(
    endpoint: str,
    sample_size: int = 10
) -> Dict[str, Any]:
    """
    Verify data quality and structure for a specific endpoint.
    
    Args:
        endpoint: Endpoint to verify (e.g., "/api/v1/inventory")
        sample_size: Number of sample records to analyze
    
    Returns:
        Data quality assessment for the specified endpoint
    """
    
    try:
        # Make API call to get data
        result = make_api_call(endpoint)
        
        if not result.get("success"):
            return {
                "error": True,
                "message": f"Unable to fetch data from endpoint: {endpoint}",
                "endpoint": endpoint
            }
        
        data = result.get("data", {})
        
        # Analyze data structure and quality
        quality_assessment = {
            "endpoint": endpoint,
            "response_status": "success",
            "data_type": type(data).__name__,
            "has_data": bool(data),
            "response_size_bytes": len(str(data)),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        # Specific analysis based on endpoint type
        if "/inventory" in endpoint:
            if isinstance(data, dict) and "ingredient_items" in data:
                items = data.get("ingredient_items", [])
                quality_assessment.update({
                    "total_records": len(items),
                    "sample_records": items[:sample_size],
                    "required_fields_present": all(
                        item.get("name") and item.get("price") is not None and item.get("available_qty") is not None
                        for item in items[:sample_size]
                    ),
                    "data_completeness": "high" if len(items) > 0 else "no_data",
                    "field_analysis": {
                        "has_names": all("name" in item for item in items[:sample_size]),
                        "has_prices": all("price" in item for item in items[:sample_size]),
                        "has_quantities": all("available_qty" in item for item in items[:sample_size]),
                        "has_status": all("stock_status" in item for item in items[:sample_size])
                    }
                })
        
        elif "/cookbook" in endpoint:
            if isinstance(data, dict) and "data" in data:
                items = data.get("data", [])
                quality_assessment.update({
                    "total_records": len(items),
                    "sample_records": items[:sample_size],
                    "required_fields_present": all(
                        item.get("name") and item.get("type") and item.get("price") is not None
                        for item in items[:sample_size]
                    ),
                    "data_completeness": "high" if len(items) > 0 else "no_data",
                    "field_analysis": {
                        "has_names": all("name" in item for item in items[:sample_size]),
                        "has_types": all("type" in item for item in items[:sample_size]),
                        "has_prices": all("price" in item for item in items[:sample_size]),
                        "has_recipes": all("recipe" in item for item in items[:sample_size])
                    }
                })
        
        elif "/wastage" in endpoint:
            quality_assessment.update({
                "has_cost_data": "total_cost" in data,
                "has_summary_data": "summary" in data or "data" in data,
                "data_completeness": "high" if data else "no_data"
            })
        
        # Overall quality score
        quality_score = 0
        if quality_assessment.get("has_data"):
            quality_score += 25
        if quality_assessment.get("total_records", 0) > 0:
            quality_score += 25
        if quality_assessment.get("required_fields_present"):
            quality_score += 25
        if quality_assessment.get("data_completeness") == "high":
            quality_score += 25
        
        quality_assessment["overall_quality_score"] = quality_score
        quality_assessment["quality_rating"] = (
            "Excellent" if quality_score >= 90 else
            "Good" if quality_score >= 70 else
            "Fair" if quality_score >= 50 else
            "Poor"
        )
        
        return {
            "success": True,
            "data_quality_assessment": quality_assessment,
            "data_source": f"Direct data quality analysis of {endpoint}",
            "confidence": "High - Based on actual endpoint response",
            "source_endpoints": [endpoint],
            "calculation_method": "Data structure and completeness analysis",
            "data_freshness": "Real-time",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Data quality verification failed: {str(e)}",
            "tool": "verify_endpoint_data_quality",
            "endpoint": endpoint
        }
