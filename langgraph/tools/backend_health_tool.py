"""
Backend Health Check Tool for LangGraph
Tests connectivity to the inventory backend API
"""

from langchain_core.tools import tool
import requests
import os
from typing import Dict, Any

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
X_TENANT_ID = os.getenv("X_TENANT_ID", "11111111-1111-1111-1111-111111111111")

@tool
def check_backend_status() -> Dict[str, Any]:
    """
    Check if the backend inventory API is available and responsive.
    Uses the health endpoint specified in contract.md: /api/v1/healthz
    
    Returns:
        Backend availability status and connection details
    """
    
    try:
        # Use the correct health endpoint from contract.md
        health_url = f"{BASE_URL}/api/v1/healthz"
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            return {
                "success": True,
                "backend_available": True,
                "status": "connected",
                "base_url": BASE_URL,
                "health_endpoint": "/api/v1/healthz",
                "response": response.json() if response.content else {"status": "ok"}
            }
        else:
            return {
                "success": False,
                "backend_available": False,
                "status": "unreachable",
                "status_code": response.status_code,
                "base_url": BASE_URL,
                "message": f"Backend returned status {response.status_code}"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "backend_available": False,
            "status": "connection_failed",
            "base_url": BASE_URL,
            "message": f"Cannot connect to backend API at {BASE_URL}. Make sure the inventory backend is running on port 8000."
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "backend_available": False,
            "status": "timeout",
            "base_url": BASE_URL,
            "message": "Backend API request timed out"
        }
    except Exception as e:
        return {
            "success": False,
            "backend_available": False,
            "status": "error",
            "base_url": BASE_URL,
            "message": f"Unexpected error: {str(e)}"
        }

@tool  
def get_available_endpoints() -> Dict[str, Any]:
    """
    List all available endpoints from contract.md that the AI agent can use.
    
    Returns:
        List of available API endpoints and their purposes
    """
    
    backend_health = check_backend_status.invoke({})
    
    return {
        "success": True,
        "backend_status": backend_health,
        "available_endpoints": {
            "inventory_analysis": {
                "get_all_inventory": "GET /api/v1/inventory - Get all inventory with stock status for analysis",
                "get_product_inventory": "GET /api/v1/inventory/{product_id} - Get specific product inventory details",
                "description": "READ-ONLY: Access current stock levels, batch info, and status for sales analysis"
            },
            "recipe_analysis": {
                "list_recipes": "GET /api/v1/cookbook/ - List all cookbook entries for menu analysis",
                "get_recipe": "GET /api/v1/cookbook/{product_id} - Get specific recipe details",
                "description": "READ-ONLY: Access recipe and menu item data for analysis"
            },
            "system_health": {
                "health_check": "GET /api/v1/healthz - Backend health status",
                "description": "System health monitoring"
            }
        },
        "analytics_note": "Sales analytics assistant uses ONLY GET endpoints for read-only analysis",
        "excluded_endpoints": "POST/PUT/DELETE operations removed - analytics should not modify backend data",
        "note": "Sales analytics endpoints are not defined in contract.md, so we simulate using inventory data",
        "tenant_id": X_TENANT_ID,
        "base_url": BASE_URL
    }
