from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database tables exist (convenient for local SQLite testing)
    try:
        from app.database.connection import Base, engine
        import app.models  # Ensures models are imported and registered
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Startup table initialization note: {e}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="ShopEase Product Catalog Microservice with Category, Search, and Inventory Management",
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
    """Health check endpoint to verify Product Catalog Service availability."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "port": settings.APP_PORT,
    }


from app.routers.category_routes import router as category_router
from app.routers.product_routes import router as product_router
from app.routers.inventory_routes import router as inventory_router

# Include API Routers
app.include_router(category_router)
app.include_router(product_router)
app.include_router(inventory_router)


