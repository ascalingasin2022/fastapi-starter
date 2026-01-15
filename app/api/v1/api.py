from fastapi import APIRouter

from app.api.v1.endpoints import health
from app.api.v1.endpoints import users
from app.api.v1.endpoints import auth  
from app.api.v1.endpoints import rbac

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication (Optional)"])
api_router.include_router(rbac.router, prefix="/rbac", tags=["RBAC Management"])

# This is the main API router that includes all endpoint routers
# Note: Authentication has been removed - all endpoints are now publicly accessible