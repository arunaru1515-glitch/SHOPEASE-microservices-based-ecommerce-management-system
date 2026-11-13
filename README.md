# ShopEase – Microservices-Based E-Commerce Platform

A modular, scalable, and independent microservices-based e-commerce platform built with **Python 3.11**, **FastAPI**, **MySQL 8**, **SQLAlchemy**, **Alembic**, and **Docker**.

Each service follows the **Database-per-Service** pattern with independent database configurations, migrations, and isolated Docker containers, secured via **JWT Role-Based Access Control (RBAC)**.

---

## 🧭 Service Registry & Port Allocation

| Service | Directory | App Port | Database | Purpose | Swagger UI |
|---|---|:---:|:---:|---|:---:|
| **Authentication Service** | [`shopease-auth-service/`](./shopease-auth-service) | `8001` | MySQL 8 (`3307`) | User Registration, Login & JWT Token Issuance | [Docs](http://localhost:8001/docs) |
| **User Management Service** | [`shopease-user-service/`](./shopease-user-service) | `8002` | MySQL 8 (`3308`) | Customer Profiles, Address Book & Default Address | [Docs](http://localhost:8002/docs) |
| **Product Service** | [`shopease-product-service/`](./shopease-product-service) | `8003` | In-Memory | Fast-prototyping Product API with Filtering & Pagination | [Docs](http://localhost:8003/docs) |
| **Product Catalog Service** | [`shopease-product-catalog-service/`](./shopease-product-catalog-service) | `8004` | MySQL 8 (`3309`) | Categories, Products, Stock IN/OUT & Audit History | [Docs](http://localhost:8004/docs) |

---

## 🛠️ Technology Stack

- **Framework:** FastAPI (Python 3.11)
- **Database:** MySQL 8.0 & SQLite / In-Memory (for testing)
- **ORM & Migrations:** SQLAlchemy 2.0 & Alembic
- **Authentication:** JWT (PyJWT, HS256)
- **Data Validation:** Pydantic v2
- **Containerization:** Docker & Docker Compose
- **Testing:** Swagger UI, Postman, Automated Scenario Test Suites

---

## 📦 Microservices Summary

### 1. Authentication Microservice (`shopease-auth-service`)
- **Port:** `8001` | **Database:** `shopease_auth_db` (`localhost:3307`)
- **Key APIs:**
  - `POST /api/auth/register` - Register customer or admin accounts with password hashing (bcrypt).
  - `POST /api/auth/login` - Authenticate credentials and issue signed JWT access tokens.
  - `GET /api/auth/me` - Retrieve current authenticated user details.

### 2. User Management Microservice (`shopease-user-service`)
- **Port:** `8002` | **Database:** `shopease_user_db` (`localhost:3308`)
- **Key APIs:**
  - `/api/users/profile` - Create, view, update, and manage customer personal details.
  - `/api/users/addresses` - Add multiple delivery addresses and switch default shipping address.
  - `/api/users/account/deactivate` - Soft-deactivation and reactivation of accounts.

### 3. Product Microservice (`shopease-product-service`)
- **Port:** `8003` | **Storage:** In-Memory Storage
- **Key APIs:**
  - `POST /api/products/` - Add products.
  - `GET /api/products/` - List products with category filtering and pagination.
  - `GET /api/products/{id}` - Retrieve product details.
  - `PUT /api/products/{id}` & `DELETE /api/products/{id}` - Update and remove products.

### 4. Product Catalog Microservice (`shopease-product-catalog-service`)
- **Port:** `8004` | **Database:** `shopease_product_catalog_db` (`localhost:3309`)
- **Key APIs:**
  - `/api/categories/` - Category CRUD with duplicate prevention and deletion protection.
  - `/api/products/` - Product management with search, category filtering, price range, and pagination.
  - `/api/inventory/{id}/stock-in` - Atomic stock intake with audit trail logging.
  - `/api/inventory/{id}/stock-out` - Atomic stock dispatch with row locking and negative stock protection.
  - `/api/inventory/{id}/history` - Reverse-chronological audit log of all stock adjustments.
  - `/api/inventory/low-stock` - Threshold-based low-stock inventory reports.

---

## 🔒 Authentication & Role-Based Access Control (RBAC)

All microservices validate incoming requests using a shared JWT standard:
- **Algorithm:** `HS256`
- **Shared Secret:** `supersecretjwtkey_change_in_production_1234567890!@#$%`
- **Roles:**
  - **Administrator (`admin`):** Full CRUD access on categories, products, inventory adjustments, and stock history.
  - **Customer (`customer`):** View active products, browse categories, check stock availability, and manage own profile/addresses.
  - **Unauthorized:** Returns HTTP `401 Unauthorized` for missing/invalid tokens, and HTTP `403 Forbidden` for insufficient privileges.

---

## 🚀 How to Run with Docker

Ensure **Docker Desktop** is open, then start any service:

```bash
# 1. Product Catalog Service (Port 8004)
cd shopease-product-catalog-service
docker-compose up --build -d

# 2. User Management Service (Port 8002)
cd ../shopease-user-service
docker-compose up --build -d

# 3. Authentication Service (Port 8001)
cd ../shopease-auth-service
docker-compose up --build -d

# 4. Product Service (Port 8003)
cd ../shopease-product-service
docker build -t shopease-product-service .
docker run -d -p 8003:8003 --name shopease-product-service shopease-product-service
```

---

## 🧪 Testing

### Automated Test Suites
Run the automated test runner in each microservice directory:

```bash
# Product Catalog Service (21/21 Scenarios Passed - 100%)
cd shopease-product-catalog-service
python tests/run_all_scenarios.py

# User Management Service (17/17 Scenarios Passed - 100%)
cd ../shopease-user-service
python tests/run_all_scenarios.py

# Product Service
cd ../shopease-product-service
pytest tests/
```

### Postman Collections
Pre-configured collections with tokens and sample requests are included in each folder:
- [`shopease_product_catalog_service.postman_collection.json`](./shopease-product-catalog-service/shopease_product_catalog_service.postman_collection.json)
- [`shopease_user_service.postman_collection.json`](./shopease-user-service/shopease_user_service.postman_collection.json)
- [`shopease_auth_service.postman_collection.json`](./shopease-auth-service/shopease_auth_service.postman_collection.json)
- [`shopease_product_service.postman_collection.json`](./shopease-product-service/shopease_product_service.postman_collection.json)
