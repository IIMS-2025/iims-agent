"""
Report Generation Tool for LangGraph
Generates comprehensive sales and performance reports
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
def generate_sales_report(
    report_type: str = "comprehensive",
    time_period: str = "last_month",
    include_forecasts: bool = True,
    include_recommendations: bool = True,
    format_type: str = "summary"
) -> Dict[str, Any]:
    """
    Generate comprehensive sales and performance reports.
    
    Args:
        report_type: Type of report (comprehensive, summary, performance, trends)
        time_period: Period for the report (last_week, last_month, last_quarter)
        include_forecasts: Include forecast data in the report
        include_recommendations: Include business recommendations
        format_type: Output format (summary, detailed, executive)
    
    Returns:
        Formatted report with metrics, insights, and recommendations
    """
    
    try:
        # Get inventory data first to verify backend connectivity
        inventory_data = make_api_call("/api/v1/inventory")
        
        if inventory_data.get("error"):
            return {
                "error": True,
                "message": f"Unable to connect to backend server: {inventory_data.get('message')}",
                "endpoint": "/api/v1/inventory",
                "suggestion": "Please ensure the inventory backend API is running on port 8000"
            }
            
        # Sales report generation requires comprehensive sales and analytics data which is not available in contract.md endpoints
        return {
            "error": True,
            "message": "Unable to connect to backend server - sales report generation requires comprehensive sales and analytics data",
            "endpoint": "No sales analytics endpoints available in contract.md",
            "suggestion": "Please ensure the inventory backend API is running on port 8000 and includes sales/analytics endpoints"
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Report generation failed: {str(e)}",
            "tool": "generate_sales_report"
        }