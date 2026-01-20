from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Callable
from functools import wraps
from app.core.casbin_enforcer import casbin_enforcer
from app.core.security import decode_access_token

security = HTTPBearer()

class AuthorizationMiddleware:
    """Middleware for handling authorization checks"""
    
    @staticmethod
    async def verify_token(credentials: HTTPAuthorizationCredentials) -> dict:
        """Verify JWT token and extract user information"""
        try:
            token = credentials.credentials
            payload = decode_access_token(token)
            return payload
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    async def check_rbac_permission(user: dict, resource: str, action: str) -> bool:
        """Check RBAC permission for user"""
        username = user.get("sub")
        return casbin_enforcer.check_rbac_permission(username, resource, action)
    
    @staticmethod
    async def check_abac_permission(user: dict, resource: str, action: str) -> bool:
        """Check ABAC permission based on user attributes"""
        attributes = {
            "department": user.get("department"),
            "level": user.get("level"),
            "location": user.get("location"),
        }
        return casbin_enforcer.check_abac_permission(attributes, resource, action)
    
    @staticmethod
    async def check_rebac_permission(user: dict, resource: str, action: str) -> bool:
        """Check ReBAC permission based on resource relationships"""
        username = user.get("sub")
        return casbin_enforcer.check_rebac_permission(username, resource, action)


def require_rbac_permission(resource: str, action: str):
    """Decorator to require RBAC permission"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get('request') or args[0]
            
            # Get authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing or invalid authorization header"
                )
            
            # Extract and verify token
            token = auth_header.split(' ')[1]
            try:
                payload = decode_access_token(token)
                username = payload.get("sub")
                
                # Check RBAC permission
                has_permission = casbin_enforcer.check_rbac_permission(
                    username, resource, action
                )
                
                if not has_permission:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions"
                    )
                
                # Add user info to request state
                request.state.user = payload
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_abac_permission(resource: str, action: str):
    """Decorator to require ABAC permission"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get('request') or args[0]
            
            # Get authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing or invalid authorization header"
                )
            
            # Extract and verify token
            token = auth_header.split(' ')[1]
            try:
                payload = decode_access_token(token)
                
                # Build attributes
                attributes = {
                    "department": payload.get("department"),
                    "level": payload.get("level"),
                    "location": payload.get("location"),
                }
                
                # Check ABAC permission
                has_permission = casbin_enforcer.check_abac_permission(
                    attributes, resource, action
                )
                
                if not has_permission:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions based on attributes"
                    )
                
                # Add user info to request state
                request.state.user = payload
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_rebac_permission(resource: str, action: str):
    """Decorator to require ReBAC permission"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get('request') or args[0]
            
            # Get authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing or invalid authorization header"
                )
            
            # Extract and verify token
            token = auth_header.split(' ')[1]
            try:
                payload = decode_access_token(token)
                username = payload.get("sub")
                
                # Check ReBAC permission
                has_permission = casbin_enforcer.check_rebac_permission(
                    username, resource, action
                )
                
                if not has_permission:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions based on resource relationships"
                    )
                
                # Add user info to request state
                request.state.user = payload
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator