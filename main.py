import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.core.config import settings
from app.core.casbin_enforcer import casbin_enforcer
from app.api.v1.endpoints import auth, rbac
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
        description="FastAPI project with RBAC, ABAC, and ReBAC authorization",
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token in the format: **your-token-here** (without 'Bearer' prefix)"
        }
    }
    
    # Apply security globally (optional, can be done per endpoint)
    # openapi_schema["security"] = [{"HTTPBearer": []}]
    
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

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(rbac.router, prefix=f"{settings.API_V1_STR}/rbac", tags=["RBAC Management"])


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
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"🚀 Starting server on port {port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )