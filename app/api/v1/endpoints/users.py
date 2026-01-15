from typing import List
from fastapi import APIRouter, Depends

from app.dependencies.services import get_user_service
from app.dtos.custom_response_dto import CustomResponse
from app.schemas.user import UserResponse
from app.services.user_service import UserService
from app.utils.response import create_response

router = APIRouter()

@router.get(
    "/",
    response_model=CustomResponse[List[UserResponse]],
    summary="Get all users",
    description="Get a list of users"
)
async def get_users(
    user_service: UserService = Depends(get_user_service)
) -> CustomResponse[List[UserResponse]]:
    users = await user_service.get_all_users()

    if not users:
        return create_response(
            data=None
        )
    
    return create_response(
        data=[UserResponse.from_orm(user) for user in users]
    )

@router.get(
    "/by-email",
    response_model=CustomResponse[UserResponse],
    summary="Get user by email",
    description="Get a user by their email address"
)
async def get_user_by_email(
    email: str,
    user_service: UserService = Depends(get_user_service)
) -> CustomResponse[UserResponse]:
    user = await user_service.get_by_email(email)

    if not user:
        return create_response(
            data=None
        )
    
    return create_response(
        data=UserResponse.from_orm(user)
    )

@router.get(
    "/{id}",
    response_model=CustomResponse[UserResponse],
    summary="Get user by ID",
    description="Get a user by their ID"
)
async def get_user_by_id(
    id: int,
    user_service: UserService = Depends(get_user_service)
) -> CustomResponse[UserResponse]:
    user = await user_service.get(id)

    if not user:
        return create_response(
            data=None
        )
    
    return create_response(
        data=UserResponse.from_orm(user)
    )
