import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.core.config import settings
from app.core.casbin_enforcer import casbin_enforcer
from app.api.v1.api import api_router
from app.db.session import engine
from app.db.base_class import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    print("🚀 Starting application...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize Casbin enforcers
    await casbin_enforcer.initialize()
    
    print("✅ Application started successfully!")
    print(f"📚 API Documentation: http://localhost:8000{settings.API_V1_STR}/docs")
    
    yield
    
    # Shutdown
    await engine.dispose()
    print("👋 Application shutdown complete")


# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
    swagger_ui_parameters={
        "persistAuthorization": True,
    }
)


def custom_openapi():
    """Custom OpenAPI schema with security definitions"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="FastAPI project with RBAC, ABAC, and ReBAC authorization using Casbin and PostgreSQL",
        routes=app.routes,
    )
    
    # No authentication required - remove security schemes
    # openapi_schema["components"]["securitySchemes"] = {
    #     "HTTPBearer": {
    #         "type": "http",
    #         "scheme": "bearer",
    #         "bearerFormat": "JWT",
    #         "description": "Enter your JWT token (login at /auth/login to get a token)"
    #     }
    # }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Set custom OpenAPI schema
app.openapi = custom_openapi

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router (includes all endpoint routers)
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to FastAPI RBAC/ABAC/ReBAC API",
        "docs": f"{settings.API_V1_STR}/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )