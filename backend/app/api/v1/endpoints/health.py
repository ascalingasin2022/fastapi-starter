from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.utils.common import log_error
from app.utils.response import create_response

router = APIRouter()

@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    description="Simple health check endpoint to verify the API is running",
)
def health_check(request: Request, db: Session = Depends(get_db)):
    """
    Health check endpoint.

    This endpoint checks the health of the service and its dependencies.
    It verifies database connectivity and returns status information.

    Args:
        request: FastAPI request object
        db: Database session dependency

    Returns:
        Success response with health status
    """
    origin = request.headers.get('origin', 'No origin')
    log_error(f"Health check performed from origin: {origin}")
    
    # Try to connect to the database
    try:
        # test database connectivity using SQLAlchemy text()
        result = db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    data = {
        "status": "ok",
        "message": "Service is healthy",
        "database": db_status,
        "version": "0.1.0"
    }

    return create_response(
        data=data,
        message="Health check successful"
    )