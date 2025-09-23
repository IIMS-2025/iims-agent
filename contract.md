# API Contract – Enhanced Inventory & Product Management

This document defines the agreed API endpoints, request formats, and responses for frontend–backend integration.
All requests must include the required headers and follow the specifications below.

## 🚀 Latest Updates

- **Enhanced Inventory Management**: Added 5 stock statuses (`in_stock`, `low_stock`, `out_of_stock`, `expiring_soon`, `dead_stock`)
- **Batch & Expiry Tracking**: Full batch management with expiry date monitoring
- **Stock Status Summary**: Aggregate counts for each status in inventory list response
- **Optimized Seed Data**: 29 products (20 raw + 3 sub + 6 menu) with comprehensive test scenarios
- **S3 Integration**: Menu image management with LocalStack support

---

## 🔑 Common Requirements

- **Base URL**: `{{base_url}}` (example: `http://localhost:8000`)
- **Test Tenant ID**: `11111111-1111-1111-1111-111111111111` (use this for testing)
- **Headers**:

  - `X-Tenant-ID: 11111111-1111-1111-1111-111111111111`
  - `Content-Type: application/json` (for raw JSON)

- **Frontend Environment Variables** (for S3 image handling):
  ```env
  ASSET_PREFIX= http://localhost:4566/iims-media/
  ```

---

## 📦 Product Creation

### 1. Create Raw Material

**POST** `/api/v1/product/create-item`
**Body (JSON):**

```json
{
  "name": "Fresh Tomatoes",
  "type": "raw_material",
  "unit": "kg",
  "price": 5.99,
  "category": "vegetables",
  "initial_qty": 10.0
}
```

**Response (Success):**

```json
{
  "data": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "location_id": "uuid",
      "name": "Fresh Tomatoes",
      "type": "raw_material",
      "unit": "kg",
      "price": "5.99",
      "category": "vegetables",
      "inventory_id": "uuid",
      "available_qty": "10.000",
      "cookbook_id": null,
      "instructions": null,
      "created_by": null,
      "image_path": null,
      "ingredients": null
    }
  ]
}
```

**Response (Error):**

```json
{
  "data": [{}],
  "errors": {
    "message": "Product with name 'Fresh Tomatoes' already exists for this tenant"
  }
}
```

---

### 2. Create Sub Product (with file upload)

**POST** `/api/v1/product/create-item`
**Body (form-data):**

- `name` (text)
- `type = sub_product`
- `unit` (text)
- `price` (text)
- `category` (text)
- `ingredients_json` (text, array of `{product_id, qty, unit}`)
- `instructions` (text)
- `image` (file)

**Response (Success):**

```json
{
  "data": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "location_id": "uuid",
      "name": "Pizza Dough",
      "type": "sub_product",
      "unit": "kg",
      "price": "8.50",
      "category": "menu",
      "inventory_id": null,
      "available_qty": "0",
      "cookbook_id": "uuid",
      "instructions": "Mix ingredients to form dough",
      "created_by": "Chef Ramsay",
      "image_path": "menu/uuid-filename.jpg",
      "ingredients": [
        {
          "product_id": "uuid",
          "product_name": "Flour",
          "qty": 1.0,
          "unit": "kg",
          "inventory_id": "uuid",
          "available_qty": 50.0
        }
      ]
    }
  ]
}
```

---

### 3. Create Menu Item (with file upload)

**POST** `/api/v1/product/create-item`
**Body (form-data):**

- `name` (text)
- `type = menu_item`
- `unit` (pcs)
- `price` (text)
- `category` (text)
- `ingredients_json` (text)
- `instructions` (text, cooking steps)
- `image` (file)

**Response (Success):**

```json
{
  "data": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "location_id": "uuid",
      "name": "Kerala Burger",
      "type": "menu_item",
      "unit": "pcs",
      "price": "299.00",
      "category": "menu",
      "inventory_id": null,
      "available_qty": "0",
      "cookbook_id": "uuid",
      "instructions": "Prepare Kerala-style burger with spices",
      "created_by": "Chef Ramsay",
      "image_path": "menu/uuid-filename.jpg",
      "ingredients": [
        {
          "product_id": "uuid",
          "product_name": "Ground Beef",
          "qty": 0.15,
          "unit": "kg",
          "inventory_id": "uuid",
          "available_qty": 25.0
        }
      ]
    }
  ]
}
```

---

## 📖 Cookbook Management

### 1. List Cookbook Items

**GET** `/api/v1/cookbook/`

**Response (Success):**

```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Kerala Burger",
      "type": "menu_item",
      "unit": "pcs",
      "price": "299.00",
      "category": "menu",
      "instructions": "Prepare Kerala-style burger with spices",
      "image_path": "menu/uuid-filename.jpg",
      "image_url": "http://localhost:4566/menu-items/menu/uuid-filename.jpg",
      "ingredients": [
        {
          "product_id": "uuid",
          "product_name": "Ground Beef",
          "qty": 0.15,
          "unit": "kg"
        }
      ]
    }
  ]
}
```

---

### 2. Get Cookbook Item by ID

**GET** `/api/v1/cookbook/{product_id}`

**Response (Success):**

```json
{
  "data": [
    {
      "name": "Classic Kerala Burger",
      "price": "299.00",
      "instructions": "1. Toast bun halves lightly. 2. Spread special sauce on bottom bun...",
      "created_by": "Ravi Nair",
      "image_path": "menu/uuid-filename.jpg",
      "image_url": "http://localhost:4566/iims-media/menu/uuid-filename.jpg",
      "ingredient_ids": ["uuid1", "uuid2", "uuid3"]
    }
  ]
}
```

---

### 3. Update Cookbook Item

**PUT** `/api/v1/cookbook/{product_id}`
**Body (form-data, optional fields):**

- `name` (text)
- `instructions` (text)
- `price` (text)
- `ingredients` (text, array JSON)
- `image` (file)

---

### 4. Delete Cookbook Item

**DELETE** `/api/v1/cookbook/{product_id}`

---

### 5. Generate Cookbook from Image (AI)

**POST** `/api/v1/cookbook/generate`
**Body (form-data):**

- `image` (file)

---

## 📊 Enhanced Inventory Management

### 1. Get All Inventory (Enhanced with Stock Status & Summary)

**GET** `/api/v1/inventory`

**Response (Success):**

```json
{
  "inventory_items": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "name": "Burger Buns",
      "type": "raw_material",
      "unit": "pcs",
      "price": "25.00",
      "category": "Bakery",
      "inventory_id": "uuid",
      "location_id": "uuid",
      "available_qty": "35.000",
      "reorder_point": "50.000",
      "critical_point": "20.000",
      "last_updated": "2025-09-22T10:54:13.998857+00:00",
      "stock_status": "low_stock",
      "earliest_expiry_date": "2025-09-24T23:59:59+00:00",
      "has_recent_activity": true,
      "batches": [
        {
          "batch": "BUNS-LOW-002",
          "expiry_date": "2025-09-24T23:59:59+00:00",
          "total_qty": "35.000",
          "unit": "pcs",
          "last_transaction": "2025-09-22T09:56:31.386384+00:00"
        }
      ]
    },
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "name": "Lettuce",
      "type": "raw_material",
      "unit": "kg",
      "price": "45.00",
      "category": "Vegetables",
      "inventory_id": "uuid",
      "location_id": "uuid",
      "available_qty": "15.000",
      "reorder_point": "5.000",
      "critical_point": "2.000",
      "last_updated": "2025-09-22T10:54:13.998857+00:00",
      "stock_status": "expiring_soon",
      "earliest_expiry_date": "2025-09-23T12:00:00+00:00",
      "has_recent_activity": true,
      "batches": [
        {
          "batch": "LET-EXP-002",
          "expiry_date": "2025-09-23T12:00:00+00:00",
          "total_qty": "15.000",
          "unit": "kg",
          "last_transaction": "2025-09-22T09:56:31.386384+00:00"
        }
      ]
    },
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "name": "Pickles",
      "type": "raw_material",
      "unit": "kg",
      "price": "120.00",
      "category": "Condiments",
      "inventory_id": "uuid",
      "location_id": "uuid",
      "available_qty": "10.000",
      "reorder_point": "3.000",
      "critical_point": "1.000",
      "last_updated": "2025-09-22T10:54:13.998857+00:00",
      "stock_status": "dead_stock",
      "earliest_expiry_date": null,
      "has_recent_activity": false,
      "batches": [
        {
          "batch": "PICK-OLD-001",
          "expiry_date": null,
          "total_qty": "10.000",
          "unit": "kg",
          "last_transaction": "2025-08-15T09:56:31.386384+00:00"
        }
      ]
    },
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "name": "Bacon",
      "type": "raw_material",
      "unit": "kg",
      "price": "350.00",
      "category": "Meat",
      "inventory_id": "uuid",
      "location_id": "uuid",
      "available_qty": "0.000",
      "reorder_point": "5.000",
      "critical_point": "1.000",
      "last_updated": "2025-09-22T10:54:13.998857+00:00",
      "stock_status": "out_of_stock",
      "earliest_expiry_date": null,
      "has_recent_activity": true,
      "batches": []
    }
  ],
  "summary": {
    "total_in_stock": 12,
    "total_low_stock": 4,
    "total_out_of_stock": 2,
    "total_expiring_soon": 2,
    "total_dead_stock": 2
  }
}
```

#### Stock Status Values:

- **`in_stock`**: Normal stock levels above reorder point
- **`low_stock`**: Below reorder point but above critical point
- **`out_of_stock`**: Zero or negative available quantity
- **`expiring_soon`**: Items expiring within 24 hours OR already expired
- **`dead_stock`**: No transaction activity in the last 30 days (configurable)

#### Enhanced Fields:

- **`stock_status`**: Calculated status based on quantity, expiry, and activity
- **`earliest_expiry_date`**: Soonest expiry date across all batches (null if none)
- **`has_recent_activity`**: Whether the product had transactions in last 30 days
- **`summary`**: Aggregate counts for each stock status across all inventory

---

### 2. Get Inventory by ID (Enhanced)

**GET** `/api/v1/inventory/{product_id}`

**Response (Success):**

```json
{
  "data": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "name": "Tomatoes",
      "type": "raw_material",
      "unit": "kg",
      "price": "60.00",
      "category": "Vegetables",
      "inventory_id": "uuid",
      "location_id": "uuid",
      "available_qty": "20.000",
      "reorder_point": "8.000",
      "critical_point": "3.000",
      "last_updated": "2025-09-22T10:54:13.998857+00:00",
      "stock_status": "expiring_soon",
      "earliest_expiry_date": "2025-09-23T14:30:00+00:00",
      "has_recent_activity": true,
      "batches": [
        {
          "batch": "TOM-EXP-003",
          "expiry_date": "2025-09-23T14:30:00+00:00",
          "total_qty": "20.000",
          "unit": "kg",
          "last_transaction": "2025-09-22T09:56:31.386384+00:00"
        }
      ]
    }
  ]
}
```

---

### 3. Update Stock (Single Product)

**POST** `/api/v1/stock/update-stock`
**Body (JSON):**

```json
{
  "product_id": "10000014-0000-0000-0000-000000000000",
  "qty": 30.0,
  "unit": "kg",
  "expiry_date": "2025-12-31T23:59:59Z",
  "tx_type": "purchase",
  "reason": "Testing single item update endpoint"
}
```

**Response (Success):**

```json
{
  "data": [
    {
      "expiry_date": "2025-12-31T23:59:59+00:00",
      "updated_items": [
        {
          "product_id": "uuid",
          "product_name": "Tomatoes",
          "qty": "30.0",
          "unit": "kg",
          "expiry_date": "2025-12-31T23:59:59+00:00",
          "inventory_id": "uuid",
          "transaction_id": "uuid",
          "updated_available_qty": "48.000"
        }
      ],
      "total_items_updated": 1,
      "transaction_ids": ["uuid"]
    }
  ]
}
```

**Response (Error - Validation):**

```json
{
  "data": [{}],
  "errors": {
    "message": "Opening Stock quantity (30.0 kg) cannot be greater than current available quantity (25.0 kg). Use 'purchase' transaction type to add new stock."
  }
}
```

---

### 4. Update Stock (Multiple Products)

**POST** `/api/v1/stock/update-stock`
**Body (JSON):**

```json
{
  "batch_id": "MIXED_DELIVERY_004",
  "expiry_date": "2026-06-30T23:59:59Z",
  "tx_type": "purchase",
  "items": [
    {
      "product_id": "10000008-0000-0000-0000-000000000000",
      "qty": 100.0,
      "unit": "kg",
      "reason": "Chicken"
    },
    {
      "product_id": "10000005-0000-0000-0000-000000000000",
      "qty": 15.0,
      "unit": "kg",
      "reason": "Tomatoes"
    },
    {
      "product_id": "10000010-0000-0000-0000-000000000000",
      "qty": 55.0,
      "unit": "ml",
      "reason": "New coconut oil delivery"
    }
  ]
}
```

**Response (Success):**

```json
{
  "data": [
    {
      "expiry_date": "2026-06-30T23:59:59+00:00",
      "updated_items": [
        {
          "product_id": "uuid1",
          "product_name": "Chicken",
          "qty": "100.0",
          "unit": "kg",
          "expiry_date": "2026-06-30T23:59:59+00:00",
          "inventory_id": "uuid1",
          "transaction_id": "uuid1",
          "updated_available_qty": "125.000"
        },
        {
          "product_id": "uuid2",
          "product_name": "Tomatoes",
          "qty": "15.0",
          "unit": "kg",
          "expiry_date": "2026-06-30T23:59:59+00:00",
          "inventory_id": "uuid2",
          "transaction_id": "uuid2",
          "updated_available_qty": "33.000"
        },
        {
          "product_id": "uuid3",
          "product_name": "Coconut Oil",
          "qty": "55.0",
          "unit": "ml",
          "expiry_date": "2026-06-30T23:59:59+00:00",
          "inventory_id": "uuid3",
          "transaction_id": "uuid3",
          "updated_available_qty": "10070.000"
        }
      ],
      "total_items_updated": 3,
      "transaction_ids": ["uuid1", "uuid2", "uuid3"]
    }
  ]
}
```

---

## 🌱 Optimized Seed Data Structure

The application includes comprehensive seed data for **Kochi Burger Junction** with enhanced inventory features:

### Product Hierarchy (29 Total Products)

#### Raw Materials (20 items)

- **Core Burger Ingredients (8)**: Ground Beef, Burger Buns, Cheddar Cheese, Lettuce, Tomatoes, Onions, Pickles, Chicken
- **Essential Cooking Ingredients (6)**: Potatoes, Coconut Oil, Special Sauce, Kerala Spices Mix, Coconut Milk, Ginger Garlic Paste
- **Specialty Items (4)**: Fish Fillet, Prawns, Basmati Rice, Sesame Seeds
- **Scenario Testing Items (2)**: Bacon, Mushrooms (out of stock)

#### Sub-Products (3 items)

- Spiced Beef Patty
- Kerala Chicken Patty
- Masala Fries

#### Menu Items (6 items)

- Classic Kerala Burger
- Kochi Chicken Burger
- Classic Combo
- Kochi Special Combo
- Kerala Fish Burger
- Seafood Combo

### Enhanced Inventory Features

#### Stock Status Coverage

- **Low Stock (4 items)**: Ground Beef, Burger Buns, Cheddar Cheese, Onions
- **Expiring Soon (2 items)**: Lettuce, Tomatoes
- **Dead Stock (2 items)**: Pickles, Special Sauce
- **In Stock (10 items)**: Normal healthy levels
- **Out of Stock (2 items)**: Bacon, Mushrooms

#### Batch & Expiry Tracking

- All inventory items include batch information
- Expiry dates for perishable items
- Transaction history for activity monitoring
- Enhanced stock calculations with priority logic

#### BOM Relationships

- **Level 1**: Sub-products made from raw materials
- **Level 2**: Menu items made from sub-products and raw materials
- Simplified 2-level hierarchy for efficient production
- Only `sub_product` and `raw_material` types in menu item ingredients

### Test Data Includes

- **1 Tenant**: Kochi Burger Junction
- **1 Location**: Marine Drive Outlet
- **4 Users**: Admin, Manager, Chef, Staff
- **28 Historical Orders**: 7 days of realistic order data
- **274+ Inventory Transactions**: Purchase, usage, adjustment, opening stock
- **S3 Integration**: 6 menu images uploaded to LocalStack
- **9 Cookbook Entries**: Recipes for sub-products and menu items
- **Analytics Data**: Usage patterns, sales metrics, forecasting

### Getting Started

1. Run `./start.sh` to initialize with Docker Compose
2. Access API at `http://localhost:8000`
3. Use test tenant ID: `11111111-1111-1111-1111-111111111111`
4. View enhanced inventory at `/api/v1/inventory`

---

## 🔄 Transaction Types

### Supported `tx_type` values:

- **`purchase`**: Adds quantity to existing stock
- **`opening_stock`**: Sets stock to specific value, calculates usage (must be ≤ current stock)
- **`closing_stock`**: Sets stock to specific value, calculates usage (must be ≤ current stock)
- **`usage`**: Records consumption/usage of stock
- **`adjustment`**: Manual stock adjustments
- **`wastage`**: Records waste/spoilage
- **`transfer`**: Stock transfers between locations
- **`production`**: Stock created through production
- **`optimal_usage`**: Optimal consumption calculations

### Business Rules:

- **Opening/Closing Stock**: Quantity must be ≤ current available quantity
- **Purchase**: Adds to existing stock (no upper limit)
- **Usage Calculation**: Automatic when using opening_stock/closing_stock
- **Two Transactions**: Opening/closing stock creates both main transaction + usage transaction
- **Validation**: Descriptive error messages for business rule violations
