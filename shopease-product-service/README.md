# ShopEase – Product Service

A REST API for managing products in the ShopEase microservices-based e-commerce system. Built with FastAPI and designed to support product creation, retrieval, updates, deletion, filtering, and pagination.

## Tech Stack

- Python 3.11
- FastAPI
- Pydantic
- Uvicorn
- Docker
- Pytest

## Features

- Create, view, update, and delete products
- Filter products by category
- Paginate product listings
- Validate product details
- Handle application errors with standard responses
- Provide interactive API documentation
- Run the service using Docker

## Project Structure

```text
shopease-product-service/
├── app/
│   ├── config/
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   ├── exceptions.py
│   └── main.py
├── tests/
├── Dockerfile
├── requirements.txt
└── shopease_product_service.postman_collection.json
```

## Setup and Run

### 1. Clone the repository

```bash
git clone https://github.com/arunaru1515-glitch/microservices-based-ecommerce-management-system.git
cd microservices-based-ecommerce-management-system
```

### 2. Create and activate a virtual environment

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the service

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

## API Documentation

Once the service is running:

- Swagger UI: http://localhost:8003/docs
- ReDoc: http://localhost:8003/redoc
- Health Check: http://localhost:8003/health

## Main API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/products/` | Create a product |
| GET | `/api/products/` | Get all products |
| GET | `/api/products/{product_id}` | Get a product by ID |
| PUT | `/api/products/{product_id}` | Update a product |
| DELETE | `/api/products/{product_id}` | Delete a product |

The product listing endpoint supports category filtering and pagination using `category`, `skip`, and `limit` query parameters.

## Run with Docker

Build the image:

```bash
docker build -t shopease-product-service .
```

Run the container:

```bash
docker run -d --name shopease-product-service -p 8003:8003 shopease-product-service
```

Open http://localhost:8003/docs to access the API.

## Run Tests

```bash
pytest -v
```

For live Docker API tests, start the container first and then run:

```bash
python tests/test_live_docker.py
```

## Postman

Import `shopease_product_service.postman_collection.json` into Postman to test the API endpoints.

## Note

The current product data store is in-memory. Product data is not retained after the application restarts.

## Repository

https://github.com/arunaru1515-glitch/microservices-based-ecommerce-management-system
