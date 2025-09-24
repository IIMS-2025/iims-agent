# IIMS Backend - GET Endpoints for AI Agent Analysis

This document lists all GET endpoints available in the IIMS (Inventory and Inventory Management System) backend for data fetching and analysis.

**Base URL:** `http://localhost:8000/api/v1`

## 📋 Table of Contents

- [Health Check](#health-check)
- [Tenancy Management](#tenancy-management)
- [Cookbook/Menu Management](#cookbookmenu-management)
- [Inventory Management](#inventory-management)
- [Stock Management](#stock-management)
- [Wastage Management](#wastage-management)

---

## 🔍 Health Check

### GET `/healthz`

**Purpose:** System health check  
**Headers:** None required  
**Query Parameters:** None  
**Response:**

```json
{
  "status": "ok"
}
```

---

## 🏢 Tenancy Management

### GET `/tenancy/tenants`

**Purpose:** List all tenants in the system  
**Headers:** None required  
**Query Parameters:** None  
**Response:** Array of tenant objects with `id`, `name`, `currency`, etc.

### GET `/tenancy/locations`

**Purpose:** List all locations, optionally filtered by tenant  
**Headers:** None required  
**Query Parameters:**

- `tenant_id` (UUID, optional) - Filter locations by tenant ID

**Response:** Array of location objects with `id`, `tenant_id`, `name`, `address`, etc.

### GET `/tenancy/products`

**Purpose:** List all products with filtering options  
**Headers:** None required  
**Query Parameters:**

- `tenant_id` (UUID, optional) - Filter by tenant
- `type` (ProductType, optional) - Filter by product type (`raw_material`, `sub_product`, `menu_item`)
- `category` (string, optional) - Filter by product category

**Response:** Array of product objects with `id`, `name`, `type`, `unit`, `price`, `category`, etc.

---

## 📖 Cookbook/Menu Management

### GET `/cookbook`

**Purpose:** List all cookbook items for a tenant (menu items and sub-products)  
**Headers:**

- `X-Tenant-ID` (UUID, required)

**Query Parameters:** None  
**Response:** Dictionary containing cookbook items with recipes, ingredients, and pricing

### GET `/cookbook/{product_id}`

**Purpose:** Get detailed information for a specific cookbook item  
**Headers:**

- `X-Tenant-ID` (UUID, required)

**Path Parameters:**

- `product_id` (UUID, required) - The product ID of the cookbook item

**Response:** Detailed cookbook item with ingredients, instructions, pricing, and image information

---

## 📦 Inventory Management

### GET `/inventory`

**Purpose:** Get all inventory details with product information  
**Headers:**

- `X-Tenant-ID` (UUID, optional) - If not provided, returns all inventory

**Query Parameters:** None  
**Response:** Array of inventory records with product details, quantities, locations, and batch information

### GET `/inventory/{product_id}`

**Purpose:** Get inventory details for a specific product  
**Headers:**

- `X-Tenant-ID` (UUID, optional)

**Path Parameters:**

- `product_id` (UUID, required) - The product ID to get inventory for

**Response:** Inventory details for the specific product including current stock levels, locations, and batch information

### GET `/inventory/debug/{product_id}`

**Purpose:** Debug endpoint to check what data exists for a product (useful for troubleshooting)  
**Headers:**

- `X-Tenant-ID` (UUID, optional)

**Path Parameters:**

- `product_id` (UUID, required) - The product ID to debug

**Response:** Debug information about the product's data in the system

---

## 📊 Stock Management

### GET `/stock/inventory/{product_id}`

**Purpose:** Get inventory details for a specific product (alternative endpoint)  
**Headers:**

- `X-Tenant-ID` (UUID, required)

**Path Parameters:**

- `product_id` (UUID, required) - The product ID

**Response:** Inventory details for the specific product

### GET `/stock/batch/{batch_id}/history`

**Purpose:** Get transaction history for a specific batch  
**Headers:**

- `X-Tenant-ID` (UUID, optional)

**Path Parameters:**

- `batch_id` (string, required) - The batch ID to get history for

**Response:** Array of transactions associated with the batch including dates, quantities, types, and reasons

---

## 🗑️ Wastage Management

### GET `/wastage`

**Purpose:** List wastage records with comprehensive filtering options  
**Headers:**

- `X-Tenant-ID` (UUID, required)
- `X-Location-ID` (UUID, required)

**Query Parameters:**

- `product_id` (UUID, optional) - Filter by product ID
- `reason` (WastageReason, optional) - Filter by wastage reason (`expired`, `damaged`, `theft`, `other`)
- `recorded_by` (UUID, optional) - Filter by user who recorded the wastage
- `start_date` (datetime, optional) - Filter from this date
- `end_date` (datetime, optional) - Filter to this date
- `limit` (int, optional, default=50, max=200) - Number of records to return
- `offset` (int, optional, default=0) - Number of records to skip

**Response:** Array of wastage records with product details, quantities, costs, and recording information

### GET `/wastage/{wastage_id}`

**Purpose:** Get a specific wastage record  
**Headers:**

- `X-Tenant-ID` (UUID, required)
- `X-Location-ID` (UUID, required)

**Path Parameters:**

- `wastage_id` (UUID, required) - The wastage record ID

**Response:** Detailed wastage record information

### GET `/wastage/by-inventory/{inventory_id}`

**Purpose:** Get all wastage records for a specific inventory item  
**Headers:**

- `X-Tenant-ID` (UUID, required)
- `X-Location-ID` (UUID, required)

**Path Parameters:**

- `inventory_id` (UUID, required) - The inventory ID

**Query Parameters:** (Same as `/wastage` endpoint)

- `reason`, `recorded_by`, `start_date`, `end_date`, `limit`, `offset`

**Response:** Array of wastage records for the specific inventory item

### GET `/wastage/summary`

**Purpose:** Get wastage summary statistics  
**Headers:**

- `X-Tenant-ID` (UUID, required)
- `X-Location-ID` (UUID, required)

**Query Parameters:**

- `start_date` (datetime, optional) - Summary from this date
- `end_date` (datetime, optional) - Summary to this date

**Response:** Summary statistics including total wastage cost, quantities by reason, trends, etc.

---

## 🛡️ Authentication & Headers

### Required Headers for Most Endpoints:

- `X-Tenant-ID`: UUID of the tenant (required for tenant-specific data)
- `X-Location-ID`: UUID of the location (required for location-specific operations)
- `X-User-ID`: UUID of the user (required for some operations)

### Optional Headers:

- `Content-Type`: `application/json` for JSON requests

---

## 📝 Data Types Reference

### ProductType Enum:

- `raw_material` - Base ingredients
- `sub_product` - Processed items used in recipes
- `menu_item` - Final products served to customers

### WastageReason Enum:

- `expired` - Product past expiration date
- `damaged` - Product damaged during handling
- `theft` - Product lost due to theft
- `other` - Other reasons

### Unit Types:

- Weight: `kg`, `g`, `lb`, `oz`
- Volume: `l`, `ml`, `gal`, `qt`
- Count: `pcs`, `box`, `pack`

---

## 🎯 AI Agent Usage Tips

1. **Start with Health Check**: Always verify system availability with `/healthz`
2. **Tenant Context**: Most endpoints require `X-Tenant-ID` header for multi-tenant isolation
3. **Pagination**: Use `limit` and `offset` parameters for large datasets
4. **Filtering**: Leverage query parameters for targeted data analysis
5. **Batch Analysis**: Use `/stock/batch/{batch_id}/history` for traceability analysis
6. **Wastage Analytics**: Use `/wastage/summary` for loss analysis and trends
7. **Inventory Overview**: Start with `/inventory` for system-wide inventory analysis

---

## 🔧 Sample cURL Commands

```bash
# Health check
curl "http://localhost:8000/api/v1/healthz"

# Get all inventory for a tenant
curl -H "X-Tenant-ID: 11111111-1111-1111-1111-111111111111" \
     "http://localhost:8000/api/v1/inventory"

# Get cookbook items
curl -H "X-Tenant-ID: 11111111-1111-1111-1111-111111111111" \
     "http://localhost:8000/api/v1/cookbook"

# Get wastage summary for the last 30 days
curl -H "X-Tenant-ID: 11111111-1111-1111-1111-111111111111" \
     -H "X-Location-ID: 22222222-2222-2222-2222-222222222222" \
     "http://localhost:8000/api/v1/wastage/summary?start_date=2025-08-24T00:00:00Z"
```
