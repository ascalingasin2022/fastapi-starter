from fastapi import APIRouter

from app.api.v1.endpoints import health
from app.api.v1.endpoints import users
from app.api.v1.endpoints import auth  
from app.api.v1.endpoints import rbac
from app.api.v1.endpoints import abac
from app.api.v1.endpoints import rebac
from app.api.v1.endpoints import authorization

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication (Optional)"])
api_router.include_router(rbac.router, prefix="/rbac", tags=["RBAC Management"])
api_router.include_router(abac.router, prefix="/abac", tags=["ABAC Management"])
api_router.include_router(rebac.router, prefix="/rebac", tags=["ReBAC Management"])
api_router.include_router(authorization.router, prefix="/authorization", tags=["Unified Authorization"])

# This is the main API router that includes all endpoint routers