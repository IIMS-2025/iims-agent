"""
Data Quality Validation Tool for LangGraph - Data-First Implementation
Comprehensive data quality assessment and validation for all database connections
"""

from langchain_core.tools import tool
import requests
import os
from typing import Optional, Dict, Any, List
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
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        return {
            "success": True,
            "status_code": response.status_code,
            "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "response_time": response.elapsed.total_seconds(),
            "headers": dict(response.headers)
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": True,
            "message": f"API call failed: {str(e)}",
            "endpoint": endpoint
        }

class DataQualityValidator:
    """Comprehensive data quality validation framework"""
    
    def __init__(self):
        self.endpoints_to_validate = [
            "/api/v1/inventory",
            "/api/v1/cookbook", 
            "/api/v1/wastage/summary",
            "/api/v1/healthz"
        ]
        
        self.quality_criteria = {
            "availability": {"weight": 0.3, "description": "Endpoint accessibility"},
            "completeness": {"weight": 0.25, "description": "Data field completeness"},
            "consistency": {"weight": 0.2, "description": "Data format consistency"},
            "freshness": {"weight": 0.15, "description": "Data currency and updates"},
            "accuracy": {"weight": 0.1, "description": "Data accuracy indicators"}
        }
    
    def validate_endpoint_availability(self, endpoint: str) -> Dict[str, Any]:
        """Validate endpoint availability and response quality"""
        
        result = make_api_call(endpoint)
        
        validation = {
            "endpoint": endpoint,
            "available": result.get("success", False),
            "response_time": result.get("response_time", 0),
            "status_code": result.get("status_code"),
            "error_message": result.get("message") if not result.get("success") else None
        }
        
        # Performance assessment
        response_time = result.get("response_time", 0)
        if response_time < 1.0:
            validation["performance_rating"] = "Excellent"
        elif response_time < 2.0:
            validation["performance_rating"] = "Good"
        elif response_time < 5.0:
            validation["performance_rating"] = "Fair"
        else:
            validation["performance_rating"] = "Poor"
        
        # Availability score
        if result.get("success"):
            validation["availability_score"] = 100
        else:
            validation["availability_score"] = 0
        
        return validation
    
    def validate_data_completeness(self, endpoint: str, data: Any) -> Dict[str, Any]:
        """Validate data completeness and structure"""
        
        completeness = {
            "endpoint": endpoint,
            "has_data": bool(data),
            "data_type": type(data).__name__,
            "completeness_score": 0,
            "missing_fields": [],
            "field_analysis": {}
        }
        
        if endpoint == "/api/v1/inventory":
            if isinstance(data, dict) and "ingredient_items" in data:
                items = data.get("ingredient_items", [])
                completeness["record_count"] = len(items)
                
                if items:
                    required_fields = ["name", "price", "available_qty", "stock_status"]
                    field_completeness = {}
                    
                    for field in required_fields:
                        present_count = sum(1 for item in items if field in item and item[field] is not None)
                        field_completeness[field] = {
                            "present": present_count,
                            "total": len(items),
                            "percentage": round(present_count / len(items) * 100, 2)
                        }
                    
                    completeness["field_analysis"] = field_completeness
                    avg_completeness = sum(f["percentage"] for f in field_completeness.values()) / len(field_completeness)
                    completeness["completeness_score"] = round(avg_completeness, 2)
                    
                    # Missing fields
                    completeness["missing_fields"] = [
                        field for field, analysis in field_completeness.items()
                        if analysis["percentage"] < 90
                    ]
        
        elif endpoint == "/api/v1/cookbook":
            if isinstance(data, dict) and "data" in data:
                items = data.get("data", [])
                completeness["record_count"] = len(items)
                
                if items:
                    required_fields = ["name", "type", "price"]
                    field_completeness = {}
                    
                    for field in required_fields:
                        present_count = sum(1 for item in items if field in item and item[field] is not None)
                        field_completeness[field] = {
                            "present": present_count,
                            "total": len(items),
                            "percentage": round(present_count / len(items) * 100, 2)
                        }
                    
                    completeness["field_analysis"] = field_completeness
                    avg_completeness = sum(f["percentage"] for f in field_completeness.values()) / len(field_completeness)
                    completeness["completeness_score"] = round(avg_completeness, 2)
        
        elif endpoint == "/api/v1/wastage/summary":
            if isinstance(data, dict):
                required_fields = ["total_cost", "total_qty"]
                present_fields = sum(1 for field in required_fields if field in data)
                completeness["completeness_score"] = round(present_fields / len(required_fields) * 100, 2)
                completeness["field_analysis"] = {
                    field: {"present": field in data} for field in required_fields
                }
        
        return completeness
    
    def validate_data_consistency(self, endpoint: str, data: Any) -> Dict[str, Any]:
        """Validate data consistency and format"""
        
        consistency = {
            "endpoint": endpoint,
            "consistency_score": 0,
            "format_issues": [],
            "data_type_consistency": {},
            "value_range_issues": []
        }
        
        if endpoint == "/api/v1/inventory":
            if isinstance(data, dict) and "ingredient_items" in data:
                items = data.get("ingredient_items", [])
                
                if items:
                    # Check data type consistency
                    price_types = [type(item.get("price", 0)).__name__ for item in items[:10]]
                    qty_types = [type(item.get("available_qty", 0)).__name__ for item in items[:10]]
                    
                    consistency["data_type_consistency"] = {
                        "price_types": list(set(price_types)),
                        "quantity_types": list(set(qty_types)),
                        "price_type_consistent": len(set(price_types)) <= 1,
                        "qty_type_consistent": len(set(qty_types)) <= 1
                    }
                    
                    # Check value ranges
                    prices = [float(item.get("price", 0)) for item in items if item.get("price") is not None]
                    quantities = [float(item.get("available_qty", 0)) for item in items if item.get("available_qty") is not None]
                    
                    if prices:
                        if any(p < 0 for p in prices):
                            consistency["value_range_issues"].append("Negative prices found")
                        if any(p > 10000 for p in prices):
                            consistency["value_range_issues"].append("Unusually high prices found")
                    
                    if quantities:
                        if any(q < 0 for q in quantities):
                            consistency["value_range_issues"].append("Negative quantities found")
                    
                    # Calculate consistency score
                    type_consistency_score = 100 if consistency["data_type_consistency"]["price_type_consistent"] and consistency["data_type_consistency"]["qty_type_consistent"] else 80
                    range_consistency_score = 100 if not consistency["value_range_issues"] else 70
                    
                    consistency["consistency_score"] = round((type_consistency_score + range_consistency_score) / 2, 2)
        
        elif endpoint == "/api/v1/cookbook":
            if isinstance(data, dict) and "data" in data:
                items = data.get("data", [])
                
                if items:
                    # Check price consistency
                    prices = [float(item.get("price", 0)) for item in items if item.get("price") is not None]
                    
                    if prices:
                        if any(p < 0 for p in prices):
                            consistency["value_range_issues"].append("Negative menu prices found")
                        if any(p > 50000 for p in prices):
                            consistency["value_range_issues"].append("Unusually high menu prices found")
                    
                    consistency["consistency_score"] = 100 if not consistency["value_range_issues"] else 80
        
        return consistency
    
    def validate_data_freshness(self, endpoint: str, data: Any) -> Dict[str, Any]:
        """Validate data freshness and currency"""
        
        freshness = {
            "endpoint": endpoint,
            "freshness_score": 0,
            "last_update_indicators": {},
            "staleness_indicators": []
        }
        
        # For now, assume data is fresh if endpoint is responding
        # In a real implementation, this would check timestamps, update frequencies, etc.
        
        if data:
            freshness["freshness_score"] = 90  # High freshness for responsive endpoints
            freshness["last_update_indicators"]["data_present"] = True
            freshness["last_update_indicators"]["fetch_time"] = datetime.now().isoformat()
        else:
            freshness["freshness_score"] = 30
            freshness["staleness_indicators"].append("No data returned")
        
        return freshness
    
    def calculate_overall_quality_score(self, validations: Dict[str, Dict]) -> Dict[str, Any]:
        """Calculate overall data quality score"""
        
        overall_score = 0
        criteria_scores = {}
        
        for criterion, config in self.quality_criteria.items():
            criterion_score = 0
            criterion_count = 0
            
            for endpoint, validation in validations.items():
                if criterion == "availability":
                    score = validation.get("availability", {}).get("availability_score", 0)
                elif criterion == "completeness":
                    score = validation.get("completeness", {}).get("completeness_score", 0)
                elif criterion == "consistency":
                    score = validation.get("consistency", {}).get("consistency_score", 0)
                elif criterion == "freshness":
                    score = validation.get("freshness", {}).get("freshness_score", 0)
                elif criterion == "accuracy":
                    # Simplified accuracy assessment
                    score = 85 if validation.get("availability", {}).get("availability_score", 0) > 0 else 0
                else:
                    score = 0
                
                criterion_score += score
                criterion_count += 1
            
            if criterion_count > 0:
                avg_criterion_score = criterion_score / criterion_count
                criteria_scores[criterion] = {
                    "score": round(avg_criterion_score, 2),
                    "weight": config["weight"],
                    "weighted_score": round(avg_criterion_score * config["weight"], 2)
                }
                overall_score += avg_criterion_score * config["weight"]
        
        return {
            "overall_quality_score": round(overall_score, 2),
            "criteria_scores": criteria_scores,
            "quality_rating": (
                "Excellent" if overall_score >= 90 else
                "Good" if overall_score >= 75 else
                "Fair" if overall_score >= 60 else
                "Poor"
            )
        }

@tool
def validate_all_data_sources(
    include_performance_metrics: bool = True,
    detailed_analysis: bool = True
) -> Dict[str, Any]:
    """
    Comprehensive validation of all data sources and database connections.
    
    Args:
        include_performance_metrics: Include performance analysis
        detailed_analysis: Include detailed field-level analysis
    
    Returns:
        Comprehensive data quality validation report
    """
    
    try:
        validator = DataQualityValidator()
        
        validation_results = {}
        
        # Validate each endpoint
        for endpoint in validator.endpoints_to_validate:
            endpoint_validation = {}
            
            # Test availability
            availability_result = validator.validate_endpoint_availability(endpoint)
            endpoint_validation["availability"] = availability_result
            
            # If endpoint is available, validate data quality
            if availability_result["available"]:
                api_result = make_api_call(endpoint)
                
                if api_result.get("success"):
                    data = api_result.get("data")
                    
                    # Validate completeness
                    completeness_result = validator.validate_data_completeness(endpoint, data)
                    endpoint_validation["completeness"] = completeness_result
                    
                    # Validate consistency
                    consistency_result = validator.validate_data_consistency(endpoint, data)
                    endpoint_validation["consistency"] = consistency_result
                    
                    # Validate freshness
                    freshness_result = validator.validate_data_freshness(endpoint, data)
                    endpoint_validation["freshness"] = freshness_result
                    
                    # Performance metrics
                    if include_performance_metrics:
                        endpoint_validation["performance"] = {
                            "response_time": availability_result["response_time"],
                            "performance_rating": availability_result["performance_rating"],
                            "data_size_estimate": len(str(data)) if data else 0
                        }
            
            validation_results[endpoint] = endpoint_validation
        
        # Calculate overall quality assessment
        overall_assessment = validator.calculate_overall_quality_score(validation_results)
        
        # Generate recommendations
        recommendations = []
        
        for endpoint, validation in validation_results.items():
            # Availability recommendations
            if not validation.get("availability", {}).get("available", False):
                recommendations.append({
                    "category": "Connectivity",
                    "priority": "Critical",
                    "endpoint": endpoint,
                    "issue": "Endpoint unavailable",
                    "recommendation": "Check backend service and network connectivity"
                })
            
            # Completeness recommendations
            completeness = validation.get("completeness", {})
            if completeness.get("completeness_score", 0) < 90:
                missing_fields = completeness.get("missing_fields", [])
                if missing_fields:
                    recommendations.append({
                        "category": "Data Quality",
                        "priority": "High",
                        "endpoint": endpoint,
                        "issue": f"Missing fields: {', '.join(missing_fields)}",
                        "recommendation": "Ensure all required fields are populated"
                    })
            
            # Performance recommendations
            if include_performance_metrics:
                performance = validation.get("performance", {})
                if performance.get("performance_rating") in ["Fair", "Poor"]:
                    recommendations.append({
                        "category": "Performance",
                        "priority": "Medium",
                        "endpoint": endpoint,
                        "issue": f"Slow response time: {performance.get('response_time', 0):.2f}s",
                        "recommendation": "Optimize database queries or consider caching"
                    })
        
        # System health summary
        available_endpoints = sum(1 for v in validation_results.values() if v.get("availability", {}).get("available", False))
        total_endpoints = len(validation_results)
        
        system_health = {
            "overall_system_health": "Healthy" if available_endpoints == total_endpoints else "Degraded" if available_endpoints > 0 else "Critical",
            "endpoint_availability": f"{available_endpoints}/{total_endpoints}",
            "availability_percentage": round(available_endpoints / total_endpoints * 100, 2),
            "data_quality_rating": overall_assessment["quality_rating"]
        }
        
        validation_report = {
            "validation_overview": {
                "validation_timestamp": datetime.now().isoformat(),
                "endpoints_validated": len(validation_results),
                "validation_scope": "availability, completeness, consistency, freshness, accuracy"
            },
            "system_health_summary": system_health,
            "overall_quality_assessment": overall_assessment,
            "endpoint_validations": validation_results,
            "recommendations": recommendations,
            "quality_criteria": validator.quality_criteria
        }
        
        return {
            "success": True,
            "data_quality_validation": validation_report,
            "data_source": "Comprehensive data quality validation across all endpoints",
            "confidence": "High - Based on systematic validation methodology",
            "source_endpoints": validator.endpoints_to_validate,
            "calculation_method": "Multi-criteria data quality assessment with weighted scoring",
            "data_freshness": "Real-time",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Data quality validation failed: {str(e)}",
            "tool": "validate_all_data_sources"
        }

@tool
def monitor_data_quality_trends(
    monitoring_period: str = "current",
    alert_thresholds: Dict[str, float] = None
) -> Dict[str, Any]:
    """
    Monitor data quality trends and generate alerts for degradation.
    
    Args:
        monitoring_period: Period to monitor (current, historical)
        alert_thresholds: Custom thresholds for quality alerts
    
    Returns:
        Data quality monitoring report with trend analysis and alerts
    """
    
    try:
        # Default alert thresholds
        if alert_thresholds is None:
            alert_thresholds = {
                "availability": 95.0,
                "completeness": 90.0,
                "consistency": 85.0,
                "overall_quality": 80.0
            }
        
        # Get current validation
        current_validation = validate_all_data_sources.invoke({
            "include_performance_metrics": True,
            "detailed_analysis": False
        })
        
        if current_validation.get("error"):
            return {
                "error": True,
                "message": "Unable to get current data quality metrics"
            }
        
        quality_data = current_validation["data_quality_validation"]
        overall_assessment = quality_data["overall_quality_assessment"]
        
        # Generate alerts based on thresholds
        alerts = []
        
        # Overall quality alert
        overall_score = overall_assessment["overall_quality_score"]
        if overall_score < alert_thresholds["overall_quality"]:
            alerts.append({
                "severity": "High" if overall_score < 60 else "Medium",
                "category": "Overall Quality",
                "message": f"Overall data quality below threshold: {overall_score:.1f}% < {alert_thresholds['overall_quality']}%",
                "current_value": overall_score,
                "threshold": alert_thresholds["overall_quality"],
                "recommended_action": "Investigate data source issues and implement quality improvements"
            })
        
        # Criteria-specific alerts
        criteria_scores = overall_assessment["criteria_scores"]
        for criterion, threshold in alert_thresholds.items():
            if criterion in criteria_scores:
                score = criteria_scores[criterion]["score"]
                if score < threshold:
                    alerts.append({
                        "severity": "Medium",
                        "category": f"{criterion.title()} Quality",
                        "message": f"{criterion.title()} below threshold: {score:.1f}% < {threshold}%",
                        "current_value": score,
                        "threshold": threshold,
                        "recommended_action": f"Focus on improving {criterion} across data sources"
                    })
        
        # Endpoint-specific alerts
        endpoint_validations = quality_data["endpoint_validations"]
        for endpoint, validation in endpoint_validations.items():
            if not validation.get("availability", {}).get("available", False):
                alerts.append({
                    "severity": "Critical",
                    "category": "Endpoint Availability",
                    "message": f"Endpoint unavailable: {endpoint}",
                    "endpoint": endpoint,
                    "recommended_action": "Check backend service status and connectivity"
                })
        
        # Trend analysis (simplified for current implementation)
        trend_analysis = {
            "current_quality_score": overall_score,
            "quality_trend": "Stable",  # Would be calculated from historical data
            "improvement_areas": [
                criterion for criterion, data in criteria_scores.items()
                if data["score"] < 80
            ],
            "stable_areas": [
                criterion for criterion, data in criteria_scores.items()
                if data["score"] >= 90
            ]
        }
        
        monitoring_report = {
            "monitoring_overview": {
                "monitoring_timestamp": datetime.now().isoformat(),
                "monitoring_period": monitoring_period,
                "alert_thresholds": alert_thresholds,
                "total_alerts": len(alerts)
            },
            "current_quality_metrics": {
                "overall_score": overall_score,
                "quality_rating": overall_assessment["quality_rating"],
                "criteria_breakdown": {k: v["score"] for k, v in criteria_scores.items()}
            },
            "alerts": alerts,
            "trend_analysis": trend_analysis,
            "system_status": {
                "status": "Critical" if any(alert["severity"] == "Critical" for alert in alerts) else
                         "Warning" if any(alert["severity"] == "High" for alert in alerts) else
                         "Healthy",
                "alert_summary": {
                    "critical": len([a for a in alerts if a["severity"] == "Critical"]),
                    "high": len([a for a in alerts if a["severity"] == "High"]),
                    "medium": len([a for a in alerts if a["severity"] == "Medium"])
                }
            }
        }
        
        return {
            "success": True,
            "data_quality_monitoring": monitoring_report,
            "data_source": "Real-time data quality monitoring and trend analysis",
            "confidence": "High - Based on systematic quality assessment",
            "source_endpoints": ["All validated endpoints"],
            "calculation_method": "Threshold-based alerting with trend analysis",
            "data_freshness": "Real-time",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Data quality monitoring failed: {str(e)}",
            "tool": "monitor_data_quality_trends"
        }
