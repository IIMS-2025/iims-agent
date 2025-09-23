# Analytics Capabilities - IIMS Agent

This document outlines the data analysis capabilities available through the IIMS system based on the available GET endpoints for cookbook and inventory management.

## 📊 Available Data Sources (GET Endpoints)

### 🍳 Cookbook Data

- **GET** `/api/v1/cookbook/` - Complete cookbook listing
- **GET** `/api/v1/cookbook/{product_id}` - Individual recipe details

### 📦 Inventory Data

- **GET** `/api/v1/inventory` - Enhanced inventory with analytics
- **GET** `/api/v1/inventory/{product_id}` - Individual item details

---

## ✅ What CAN Be Analyzed

### 🎯 **Real-Time Operational Analytics**

#### 1. **Stock Health Dashboard**

- **Stock Status Distribution**: Live counts of items by status
  - In Stock: `total_in_stock`
  - Low Stock: `total_low_stock`
  - Out of Stock: `total_out_of_stock`
  - Expiring Soon: `total_expiring_soon`
  - Dead Stock: `total_dead_stock`
- **Critical Alerts**: Items requiring immediate attention
- **Reorder Recommendations**: Items below reorder points

#### 2. **Expiry Management & Waste Prevention**

- **Immediate Expiry Alerts**: Items expiring within 24 hours
- **Batch-Level Tracking**: Individual batch expiry dates
- **Waste Risk Assessment**: Items approaching expiry
- **FIFO Compliance**: First-in-first-out rotation tracking

#### 3. **Inventory Activity Analysis**

- **Dead Stock Identification**: Items with no activity in 30+ days
- **Activity Monitoring**: Recent transaction patterns
- **Turnover Indicators**: Active vs. stagnant inventory
- **Usage Patterns**: Product movement frequency

#### 4. **Menu Cost Analysis**

- **Recipe Costing**: Calculate cost per menu item
- **Ingredient Usage Mapping**: Which ingredients are used where
- **Profitability Analysis**: Menu item margin calculations
- **Price Optimization**: Cost-based pricing recommendations

#### 5. **Product Portfolio Analysis**

- **Category Distribution**: Breakdown by product categories
- **Type Analysis**: Raw materials vs. sub-products vs. menu items
- **Price Range Analysis**: Cost distribution across products
- **Complexity Assessment**: Recipe ingredient count analysis

#### 6. **Bill of Materials (BOM) Intelligence**

- **Dependency Mapping**: Ingredient relationships
- **Recipe Complexity**: Number of ingredients per item
- **Sub-Product Usage**: How sub-products are utilized
- **Supply Chain Impact**: Critical ingredient identification

#### 7. **Operational Efficiency Metrics**

- **Stock Level Optimization**: Current vs. optimal levels
- **Inventory Value**: Total stock value calculations
- **Category Performance**: Performance by product category
- **Location Efficiency**: Single location analysis ready

---

## ❌ What CANNOT Be Analyzed

### 📈 **Historical & Trend Analytics**

#### 1. **Time-Series Analysis**

- **Historical Stock Movements**: No transaction history available
- **Consumption Trends**: No usage pattern over time
- **Seasonal Patterns**: No historical data for seasonality
- **Growth Trends**: No time-based inventory changes

#### 2. **Sales Performance Analytics**

- **Sales Volume**: No order/sales data in endpoints
- **Revenue Analysis**: No sales transaction data
- **Customer Preferences**: No order pattern data
- **Menu Item Performance**: No sales-based ranking

#### 3. **Financial Reporting**

- **P&L Analysis**: Limited to current stock values only
- **Cost of Goods Sold (COGS)**: No historical consumption data
- **Inventory Turnover Ratios**: No time-based calculations
- **ROI Analysis**: No investment vs. return data

#### 4. **Predictive Analytics**

- **Demand Forecasting**: No historical consumption patterns
- **Stock Prediction**: No trend data for projections
- **Reorder Optimization**: No usage velocity data
- **Seasonal Planning**: No historical seasonal data

#### 5. **Advanced Business Intelligence**

- **Supplier Performance**: No supplier data available
- **Purchase Analysis**: No purchasing history
- **Vendor Comparison**: No supplier information
- **Contract Analysis**: No procurement data

#### 6. **Multi-Location Analytics**

- **Cross-Location Comparison**: Single location data only
- **Transfer Analysis**: No inter-location movement data
- **Regional Performance**: Limited to one location
- **Distribution Optimization**: No multi-site data

---

## 🚀 Recommended Enhancements for Full Analytics

### **Additional Endpoints Needed**

#### 1. **Historical Data Endpoints**

```
GET /api/v1/analytics/inventory-history?days=30
GET /api/v1/analytics/transactions?from=date&to=date
GET /api/v1/analytics/consumption-patterns
```

#### 2. **Sales Data Endpoints**

```
GET /api/v1/analytics/sales?period=monthly
GET /api/v1/analytics/menu-performance
GET /api/v1/analytics/customer-orders
```

#### 3. **Financial Analytics Endpoints**

```
GET /api/v1/analytics/financial-summary
GET /api/v1/analytics/cogs-analysis
GET /api/v1/analytics/profitability
```

#### 4. **Predictive Analytics Endpoints**

```
GET /api/v1/analytics/forecasting
GET /api/v1/analytics/demand-prediction
GET /api/v1/analytics/reorder-suggestions
```

---

## 💡 Current Analytics Strategy

### **Focus Areas with Available Data**

1. **Real-Time Dashboards**: Leverage current stock status and summary data
2. **Operational Alerts**: Build alerts for critical stock situations
3. **Menu Optimization**: Use recipe and cost data for menu engineering
4. **Waste Reduction**: Utilize expiry tracking for waste prevention
5. **Inventory Health**: Monitor stock levels and activity patterns

### **Immediate Value Opportunities**

- **Live Stock Dashboard**: Real-time inventory status visualization
- **Alert System**: Critical stock and expiry notifications
- **Recipe Cost Calculator**: Menu item profitability analysis
- **Dead Stock Report**: Identify slow-moving inventory
- **Expiry Management**: Prevent waste through timely alerts

---

## 🎯 Conclusion

The current GET endpoints provide **excellent foundation for real-time operational analytics** but are **limited for historical and predictive analysis**. The focus should be on:

- **Immediate actionable insights** from current data
- **Operational efficiency** improvements
- **Cost optimization** through better inventory management
- **Waste reduction** through expiry monitoring

For comprehensive business intelligence and predictive analytics, additional endpoints with historical data would be required.
