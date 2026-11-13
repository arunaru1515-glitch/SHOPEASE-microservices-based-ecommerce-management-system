# ShopEase – Product Catalog Microservice with Category & Inventory Management

An independent, containerized Product Catalog Microservice built with **FastAPI**, **SQLAlchemy ORM**, **Alembic**, and **MySQL 8**. Manages product catalogs, categories, pricing, stock availability, search/filtering/pagination, and inventory transaction audit trails, secured by **JWT Role-Based Access Control (RBAC)**.

---

## 🛠️ Technology Stack

- **Backend Framework**: Python 3.11, FastAPI
- **Database**: MySQL 8.0 (Internal Port: 3306, Host Port: 3309)
- **ORM**: SQLAlchemy
- **Database Migrations**: Alembic
- **Validation**: Pydantic v2 & Pydantic Settings
- **Authentication**: JWT (Shared Secret: HS256, RBAC: Admin vs Customer)
- **Containerization**: Docker, Docker Compose
- **Testing**: Automated Scenario Test Suite (21/21 Scenarios), Postman Collection, Swagger UI

---

## 📂 Project Architecture & Folder Structure

```
shopease-product-catalog-service/
│
├── app/
│   ├── main.py                      # FastAPI app entrypoint, CORS, lifespan, and router mounting
│   │
│   ├── core/
│   │   ├── config.py                # Pydantic Settings reading .env & dynamic DB URL
│   │   └── security.py              # JWT Bearer token validation and RBAC guards (require_admin)
│   │
│   ├── database/
│   │   └── connection.py            # SQLAlchemy engine, SessionLocal, and get_db dependency
│   │
│   ├── models/
│   │   ├── category_model.py        # Categories table ORM mapping
│   │   ├── product_model.py         # Products table ORM mapping (with CheckConstraints)
│   │   └── inventory_model.py       # Inventory transactions audit log ORM mapping
│   │
│   ├── schemas/
│   │   ├── category_schema.py       # Category Pydantic schemas (Create, Update, Response)
│   │   ├── product_schema.py        # Product schemas, pricing validations, pagination
│   │   └── inventory_schema.py      # Stock adjustment, status, and audit log schemas
│   │
│   ├── services/
│   │   ├── category_service.py      # Category CRUD, duplicate checks, deletion safeguard
│   │   ├── product_service.py       # Product CRUD, search, filter, pagination, SKU checks
│   │   └── inventory_service.py     # Atomic Stock IN/OUT, row locking, low-stock reports
│   │
│   └── routers/
│       ├── category_routes.py       # Category endpoints (/api/categories/)
│       ├── product_routes.py        # Product endpoints (/api/products/)
│       └── inventory_routes.py      # Inventory endpoints (/api/inventory/)
│
├── alembic/
│   ├── env.py                       # Alembic environment configured with dynamic DB connection
│   └── versions/
│       └── 001_create_catalog_and_inventory_tables.py  # Idempotent migration script
│
├── tests/
│   ├── run_all_scenarios.py         # Automated runner executing all 21 mandatory test scenarios
│   └── test_live_docker.py          # Integration test runner against containerized service
│
├── Dockerfile                       # Python 3.11-slim container definition (Port 8004)
├── docker-compose.yml               # Multi-container orchestration (catalog-service + catalog-db)
├── shopease_product_catalog_service.postman_collection.json # Complete Postman test collection
├── requirements.txt                 # Python project dependencies
├── .env.example                     # Environment configuration template
├── .env                             # Local environment variables
├── .dockerignore
├── .gitignore
└── README.md
```

---

## 🗄️ Database Schema & Data Models

### 1. Categories Table (`categories`)
| Column | Type | Constraints & Attributes | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key, Auto-increment | Category identifier |
| `name` | String(100) | Unique, Not Null, Indexed | Category name |
| `description` | Text | Nullable | Category details |
| `is_active` | Boolean | Default True, Not Null | Category status |
| `created_at` | DateTime(tz) | Server Default `CURRENT_TIMESTAMP` | Creation timestamp |
| `updated_at` | DateTime(tz) | Server Default & OnUpdate `now()` | Last update timestamp |

### 2. Products Table (`products`)
| Column | Type | Constraints & Attributes | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key, Auto-increment | Product identifier |
| `category_id` | Integer | Foreign Key (`categories.id`), RESTRICT | Parent category |
| `name` | String(255) | Not Null, Indexed | Product name |
| `description` | Text | Nullable | Detailed product description |
| `sku` | String(100) | Unique, Not Null, Indexed | Stock Keeping Unit |
| `price` | Decimal(10,2)| Not Null, `CheckConstraint >= 0` | Product price |
| `discount_price`| Decimal(10,2)| Nullable, `CheckConstraint >= 0` | Discounted promotional price |
| `stock_quantity`| Integer | Not Null, Default 0, `Check >= 0` | Units currently available in stock |
| `image_url` | String(500) | Nullable | Product thumbnail image URL |
| `brand` | String(100) | Nullable, Indexed | Brand name |
| `is_active` | Boolean | Default True, Not Null, Indexed | Product availability flag |
| `created_at` | DateTime(tz) | Server Default `CURRENT_TIMESTAMP` | Creation timestamp |
| `updated_at` | DateTime(tz) | Server Default & OnUpdate `now()` | Last update timestamp |

### 3. Inventory Transactions Table (`inventory_transactions`)
| Column | Type | Constraints & Attributes | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key, Auto-increment | Transaction log identifier |
| `product_id` | Integer | Foreign Key (`products.id`), CASCADE | Associated product |
| `transaction_type`| String(20)| Not Null (`IN` or `OUT`) | Movement type |
| `quantity` | Integer | Not Null (`> 0`) | Number of units adjusted |
| `previous_stock`| Integer | Not Null | Stock balance before adjustment |
| `updated_stock` | Integer | Not Null | Stock balance after adjustment |
| `remarks` | String(255) | Nullable | Reason for adjustment / order reference |
| `created_at` | DateTime(tz) | Server Default `CURRENT_TIMESTAMP` | Timestamp of inventory event |

---

## 🔒 JWT Authentication & Role-Based Authorization

The Product Catalog Service shares JWT signing configuration with `shopease-auth-service`:
- **Algorithm**: `HS256`
- **Secret Key**: `supersecretjwtkey_change_in_production_1234567890!@#$%`
- **Token Claims**: `sub` (User ID), `email`, `role` (`"admin"` or `"customer"`), `iat`, `exp`

### Permission Matrix
| Endpoint Group | Method | Customer / Anonymous | Administrator |
| :--- | :--- | :--- | :--- |
| `/api/categories/` | GET | View Active Categories | View All (Active & Inactive) |
| `/api/categories/` | POST, PUT, DELETE | ❌ HTTP 403 Forbidden | ✅ Allowed |
| `/api/products/` | GET | View Active Products only | View All & Inactive Products |
| `/api/products/` | POST, PUT, PATCH, DELETE | ❌ HTTP 403 Forbidden | ✅ Allowed |
| `/api/inventory/{id}` | GET | Check stock & availability | Check stock & availability |
| `/api/inventory/...` | POST (IN/OUT), GET (history, low-stock) | ❌ HTTP 403 Forbidden | ✅ Allowed |

---

## 🚀 API Endpoints Overview

### Categories (`/api/categories/`)
- `POST /api/categories/` - Create a new category *(Admin)*
- `GET /api/categories/` - List categories *(Customers see active only)*
- `GET /api/categories/{id}` - Retrieve category details
- `PUT /api/categories/{id}` - Update category *(Admin)*
- `DELETE /api/categories/{id}` - Delete category *(Admin - blocked if products exist)*

### Products (`/api/products/`)
- `POST /api/products/` - Create a product *(Admin)*
- `GET /api/products/` - Search, filter, and paginate products *(Query params: `search`, `category_id`, `min_price`, `max_price`, `in_stock`, `sort_by`, `sort_order`, `page`, `page_size`)*
- `GET /api/products/{id}` - Retrieve product details
- `PUT /api/products/{id}` - Replace full product details *(Admin)*
- `PATCH /api/products/{id}` - Partially update product *(Admin)*
- `DELETE /api/products/{id}` - Delete product and audit logs *(Admin)*

### Inventory Management (`/api/inventory/`)
- `GET /api/inventory/{product_id}` - Get current stock and low-stock flag
- `POST /api/inventory/{product_id}/stock-in` - Increase stock atomically *(Admin)*
- `POST /api/inventory/{product_id}/stock-out` - Decrease stock atomically *(Admin - prevents negative stock)*
- `GET /api/inventory/{product_id}/history` - View complete stock modification history *(Admin)*
- `GET /api/inventory/low-stock?threshold=10` - List products below stock threshold *(Admin)*

---

## ⚙️ Running Locally & with Docker Compose

### Option A: Running with Docker Compose (Recommended)
Make sure Docker Desktop is started, then run:

```bash
cd shopease-product-catalog-service
docker-compose up --build -d
```

- **Catalog API**: `http://localhost:8004`
- **Swagger Documentation**: `http://localhost:8004/docs`
- **MySQL Database**: `localhost:3309` (Service name: `catalog-db:3306`)

To view live container logs:
```bash
docker-compose logs -f catalog-service
```

To stop containers:
```bash
docker-compose down
```

### Option B: Running Standalone with Python
```bash
cd shopease-product-catalog-service

# Apply Alembic Migrations
alembic upgrade head

# Run FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload
```

---

## 🧪 Automated Testing

### Run All 21 Mandatory Test Scenarios
```bash
python tests/run_all_scenarios.py
```

### Test Results Summary:
```
===============================================================================================
 SHOPEASE PRODUCT CATALOG SERVICE: MANDATORY TEST SCENARIOS (STEP 10)
===============================================================================================
[PASS] Scenario 01: Create a product with valid information                      - Created Product ID=1, SKU=LAPTOP-RTX-001
[PASS] Scenario 02: Create a product with duplicate SKU (HTTP 409)               - Status 409: Product with SKU 'LAPTOP-RTX-001' already exists.
[PASS] Scenario 03: Create a product with invalid category (HTTP 400)            - Status 400: Category with ID 9999 does not exist.
[PASS] Scenario 04: Create product with negative price (Validation error)        - Validation caught negative price: ValidationError
[PASS] Scenario 05: Retrieve all active products                                 - Customer active list contains 1 products, inactive excluded
[PASS] Scenario 06: Retrieve product details with invalid ID (HTTP 404)          - Status 404: Product with ID 999999 not found.
[PASS] Scenario 07: Update and partially update a product (PUT & PATCH)          - Name='Gaming Laptop Pro Max', Brand='Asus ROG Strix'
[PASS] Scenario 08: Delete or deactivate a product                               - Product 2 deleted cleanly from database
[PASS] Scenario 09: Create duplicate category (HTTP 409)                         - Status 409: Category with name 'electronics' already exists.
[PASS] Scenario 10: Retrieve products using search and filters                   - Search, category filter, and price range all verified
[PASS] Scenario 11: Test pagination and sorting (asc/desc & page limits)         - Total=2, Pages=2, Sorting verified
[PASS] Scenario 12: Increase product stock (Stock-in)                            - Stock increased: 20 -> 35
[PASS] Scenario 13: Decrease product stock (Stock-out)                           - Stock decreased: 35 -> 25
[PASS] Scenario 14: Attempt to reduce stock below zero (HTTP 400)                - Status 400: Insufficient stock for product 'Gaming Laptop Pro Max' (SKU: LAPTOP-RTX-001). Requested deduction: 999, Available: 25.
[PASS] Scenario 15: Verify inventory transaction history                         - Found 3 recorded audit transactions for Product ID=1
[PASS] Scenario 16: Retrieve low-stock products with threshold                   - Threshold=30 matched 1 products; Threshold=10 matched 0
[PASS] Scenario 17: Access administrative APIs as customer (HTTP 403)            - Status 403: Forbidden: Administrative privileges required.
[PASS] Scenario 18: Access protected APIs without JWT token (HTTP 401)           - Status 401: Authentication token is missing. Please provide Authorization: Bearer <token>
[PASS] Scenario 19: Access protected APIs with invalid token (HTTP 401)          - Status 401: Invalid authentication token.
[PASS] Scenario 20: Simultaneous updates & atomic rollback consistency           - Stock remained at 25, zero dirty transactions
[PASS] Scenario 21: Verify database records & persistence integrity              - Verified Category (Electronics), Product (Gaming Laptop Pro Max), and 3 Transactions
===============================================================================================
 FINAL SUMMARY: 21/21 SCENARIOS PASSED (100.0%)
===============================================================================================
```

### Postman Collection
Import `shopease_product_catalog_service.postman_collection.json` directly into Postman to test all endpoints interactively.

