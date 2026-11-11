from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.connection import Base, engine
import app.models  # Ensures UserProfile and UserAddress models are registered
from app.routers.user_routes import router as user_profile_router
from app.routers.address_routes import router as address_router
from app.routers.account_routes import router as account_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # For SQLite/local dev, ensure tables exist; in MySQL, Alembic manages schemas
    if not settings.get_database_url().startswith("mysql"):
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as exc:
            print(f"Database initialization warning: {exc}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="ShopEase User Management Microservice for Customer Profiles and Delivery Addresses",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Enable CORS for cross-service and frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify User Service availability."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "port": settings.APP_PORT,
    }


# Register User Management Routers under /api/users
app.include_router(user_profile_router, prefix="/api/users")
app.include_router(address_router, prefix="/api/users")
app.include_router(account_router, prefix="/api/users")
