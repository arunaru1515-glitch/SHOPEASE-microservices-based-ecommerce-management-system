from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.connection import Base, engine
import app.models  # Ensures all models are registered
from app.routers.auth_routes import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database tables exist on startup (especially helpful for local development)
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        print(f"Database initialization warning: {exc}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="ShopEase Authentication Microservice with JWT, MySQL, and Docker",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Enable CORS for cross-service communication and client applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify service availability."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }


# Register Authentication Router
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
