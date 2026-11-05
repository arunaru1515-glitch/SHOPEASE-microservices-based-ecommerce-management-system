# ShopEase – Authentication Microservice

A secure, independent Authentication Microservice for the ShopEase e-commerce platform. Built with **FastAPI**, **MySQL 8**, **SQLAlchemy**, **Alembic**, and **JWT**, containerized using **Docker** and **Docker Compose**.

---

## 🛠 Technology Stack

- **Framework:** FastAPI
- **Web Server:** Uvicorn
- **Database:** MySQL 8
- **ORM:** SQLAlchemy 2.0
- **Database Migrations:** Alembic
- **Authentication:** JWT (PyJWT)
- **Password Security:** Passlib & Bcrypt (Salting & Hashing)
- **Data Validation:** Pydantic v2 (with Email-Validator)
- **Containerization:** Docker, Docker Compose
- **Testing:** Pytest, Postman, Swagger UI

---

## 📁 Project Structure

```text
shopease-auth-service/
│
├── alembic/
│   ├── versions/
│   │   └── 001_create_users_table.py
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
│   │   └── user_model.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   └── auth_routes.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── auth_schema.py
│   │
│   └── services/
│       ├── __init__.py
│       └── auth_service.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_auth_api.py
│
├── .dockerignore
├── .env.example
├── .gitignore
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── shopease_auth_service.postman_collection.json
└── README.md
```

---

## 🗄 Database Configuration

### Database Name
`shopease_auth_db`

### `users` Table Schema
| Field | Data Type | Constraint | Description |
|---|---|---|---|
| `id` | Integer | Primary Key, Auto-increment | Unique identifier |
| `full_name` | String(255) | Non-null | User full name |
| `email` | String(255) | Unique, Indexed, Non-null | User email address |
| `password_hash` | String(255) | Non-null | Bcrypt hashed password |
| `role` | String(50) | Default: "customer" | User role |
| `is_active` | Boolean | Default: True | Account status |
| `created_at` | DateTime | Default: CURRENT_TIMESTAMP | Account creation timestamp |
| `updated_at` | DateTime | Default: CURRENT_TIMESTAMP | Last updated timestamp |

---

## ⚙️ Environment Variables

Create a `.env` file in the root directory (based on `.env.example`):

```dotenv
# Application Settings
APP_NAME=ShopEase-Auth-Service
APP_ENV=development
APP_PORT=8001

# MySQL Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=shopease_user
DB_PASSWORD=shopease_password
DB_NAME=shopease_auth_db

# JWT Configuration
JWT_SECRET_KEY=supersecretjwtkey_change_in_production_1234567890!@#$%
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Default User Role
DEFAULT_USER_ROLE=customer
```

---

## 🚀 Running with Docker Compose (Recommended)

To run the complete microservice with its dedicated MySQL database:

```bash
docker-compose up --build -d
```

This command will:
1. Start the MySQL 8 container (`shopease-auth-db`) with a persistent Docker volume (`auth_db_data`).
2. Wait for MySQL to become healthy.
3. Automatically run Alembic database migrations (`alembic upgrade head`).
4. Start the FastAPI microservice on `http://localhost:8001`.

To stop the services:
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

To create a new migration:
```bash
alembic revision --autogenerate -m "describe changes"
```

### 3. Start the Application
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

---

## 📖 API Documentation & Endpoints

Interactive Swagger UI documentation is available at:
- **Swagger UI:** `http://localhost:8001/docs`
- **ReDoc:** `http://localhost:8001/redoc`
- **Health Check:** `http://localhost:8001/health`

### Main Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/health` | Service health status | No |
| `POST` | `/api/auth/register` | Register a new user | No |
| `POST` | `/api/auth/login` | Authenticate and obtain JWT token | No |
| `GET` | `/api/auth/me` | Retrieve authenticated user profile | Yes (Bearer Token) |
| `POST` | `/api/auth/verify-token` | Validate token validity & claims | No |
| `POST` | `/api/auth/change-password`| Change authenticated user password | Yes (Bearer Token) |

---

## 🔑 JWT Authentication

When logging in via `POST /api/auth/login`, you receive an access token:

```json
{
  "message": "Login successful.",
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "role": "customer",
    "is_active": true
  }
}
```

Include this token in protected API requests via the `Authorization` header:

```http
Authorization: Bearer <access_token>
```

---

## 🧪 Testing

### Automated Pytest Suite
```bash
pytest -v
```

### Postman
Import `shopease_auth_service.postman_collection.json` into Postman to run pre-configured scenarios including registration, login, profile retrieval, and password change.

