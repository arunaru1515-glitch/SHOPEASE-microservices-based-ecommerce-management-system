# ShopEase – User Management Microservice

A secure, independent User Management Microservice for the ShopEase microservices-based e-commerce platform. Built with **FastAPI**, **MySQL 8**, **SQLAlchemy**, **Alembic**, and **JWT**, containerized using **Docker** and **Docker Compose**.

---

## 🛠 Technology Stack

- **Framework:** FastAPI
- **Web Server:** Uvicorn
- **Database:** MySQL 8
- **ORM:** SQLAlchemy 2.0
- **Database Migrations:** Alembic
- **Authentication:** JWT (PyJWT) - Integrated with Authentication Service
- **Data Validation:** Pydantic v2
- **Containerization:** Docker, Docker Compose
- **Testing:** Pytest, Postman, Swagger UI

---

## 📁 Project Structure

```text
shopease-user-service/
│
├── alembic/
│   ├── versions/
│   │   └── 001_create_user_profile_and_addresses.py
│   ├── env.py
│   ├── README
│   └── script.py.mako
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── security.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user_model.py
│   │   └── address_model.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── user_routes.py
│   │   ├── address_routes.py
│   │   └── account_routes.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user_schema.py
│   │   └── address_schema.py
│   │
│   └── services/
│       ├── __init__.py
│       ├── user_service.py
│       └── address_service.py
│
├── tests/
│   ├── run_all_scenarios.py
│   └── test_live_docker.py
│
├── .dockerignore
├── .env.example
├── .gitignore
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── shopease_user_service.postman_collection.json
└── README.md
```

---

## 🗄 Database Configuration

### Database Name
`shopease_user_db`

### 1. `user_profiles` Table
| Field | Data Type | Constraint | Description |
|---|---|---|---|
| `id` | Integer | Primary Key, Auto-increment | Unique identifier |
| `auth_user_id` | Integer | Unique, Indexed, Non-null | User ID from Authentication Service |
| `full_name` | String(255) | Non-null | Customer full name |
| `phone_number` | String(20) | Nullable | Contact number |
| `date_of_birth` | Date | Nullable | Date of birth |
| `gender` | String(20) | Nullable | Gender |
| `profile_image` | String(500) | Nullable | Profile image URL or path |
| `is_active` | Boolean | Default: True | Account status |
| `created_at` | DateTime | Default: CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | DateTime | Default: CURRENT_TIMESTAMP | Update timestamp |

### 2. `user_addresses` Table
| Field | Data Type | Constraint | Description |
|---|---|---|---|
| `id` | Integer | Primary Key, Auto-increment | Unique address identifier |
| `user_id` | Integer | Foreign Key (`user_profiles.id`), ON DELETE CASCADE | Associated user profile |
| `address_type` | String(50) | Default: "Home" | Home, Office, or Other |
| `full_name` | String(255) | Non-null | Recipient full name |
| `phone_number` | String(20) | Non-null | Contact phone number |
| `address_line_1` | String(255) | Non-null | Street address |
| `address_line_2` | String(255) | Nullable | Apartment / suite / unit |
| `city` | String(100) | Non-null | City name |
| `state` | String(100) | Non-null | State / Province |
| `country` | String(100) | Non-null | Country name |
| `postal_code` | String(20) | Non-null | Postal / ZIP code |
| `is_default` | Boolean | Default: False | Primary delivery address flag |
| `created_at` | DateTime | Default: CURRENT_TIMESTAMP | Creation timestamp |

---

## ⚙️ Environment Variables

Create a `.env` file (based on `.env.example`):

```dotenv
# Application Configuration
APP_NAME=ShopEase-User-Service
APP_ENV=development
APP_PORT=8002

# Local SQLite fallback for fast testing without MySQL on host
DATABASE_URL=sqlite:///./shopease_user.db

# MySQL Database Configuration (Used in Docker Compose container)
DB_HOST=localhost
DB_PORT=3306
DB_USER=shopease_user
DB_PASSWORD=shopease_password
DB_NAME=shopease_user_db

# JWT Configuration (Identical to Authentication Service)
JWT_SECRET_KEY=supersecretjwtkey_change_in_production_1234567890!@#$%
JWT_ALGORITHM=HS256

# Auth Microservice URL
AUTH_SERVICE_URL=http://localhost:8001
```

---

## 🔐 Authentication Service Integration

* **Zero Trust:** The User Service **never** trusts client-supplied user IDs in URL parameters or request bodies.
* User identity is strictly extracted from the `sub` claim of the verified JWT token (`Authorization: Bearer <token>`).
* Missing or expired tokens return HTTP **`401 Unauthorized`**.
* Attempting to access or modify another user's address returns HTTP **`403 Forbidden`**.

---

## 🚀 Running with Docker Compose

To start both the User Service and its dedicated MySQL 8 database:

```bash
docker-compose up --build -d
```

To stop:
```bash
docker-compose down
```

---

## 🛠 Local Development Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Database Migrations
```bash
alembic upgrade head
```

### 3. Start the Application
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

---

## 📖 API Documentation & Endpoints

Interactive Swagger UI documentation:
- **Swagger UI:** `http://localhost:8002/docs`
- **ReDoc:** `http://localhost:8002/redoc`
- **Health Check:** `http://localhost:8002/health`

### Main Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|:---:|
| `GET` | `/health` | Service health status | No |
| `POST` | `/api/users/profile` | Create customer profile | Yes |
| `GET` | `/api/users/profile` | Get current user's profile | Yes |
| `PUT` | `/api/users/profile` | Full profile update | Yes |
| `PATCH` | `/api/users/profile` | Partial profile update | Yes |
| `DELETE` | `/api/users/profile` | Delete user profile & addresses | Yes |
| `POST` | `/api/users/addresses` | Add a new delivery address | Yes |
| `GET` | `/api/users/addresses` | List addresses (default first) | Yes |
| `GET` | `/api/users/addresses/{id}` | Get specific address | Yes |
| `PUT` | `/api/users/addresses/{id}` | Update address | Yes |
| `DELETE` | `/api/users/addresses/{id}` | Delete an address | Yes |
| `PATCH` | `/api/users/addresses/{id}/default` | Set as default delivery address | Yes |
| `GET` | `/api/users/account` | Account summary dashboard | Yes |
| `PATCH` | `/api/users/account/deactivate` | Deactivate user profile | Yes |
| `PATCH` | `/api/users/account/reactivate` | Reactivate user profile | Yes |

---

## 🧪 Testing Results

### Automated Scenario Test Suite (17/17 Passed - 100%)
Run the automated test suite covering all mandatory specifications:
```bash
python tests/run_all_scenarios.py
```

### Postman Testing
Import `shopease_user_service.postman_collection.json` into Postman to run pre-configured requests with automatic `authToken` handling.

