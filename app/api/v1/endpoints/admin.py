from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_admin, get_current_staff
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.settings import SettingsResponse, SettingsUpdate
from app.schemas.user import (
    MessageResponse,
    UserCreate,
    UserResponse,
)
from app.services import auth as auth_service
from app.services import settings as settings_service

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_hr(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    try:
        return auth_service.create_hr_user(db, user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/users",
    response_model=list[UserResponse],
)
def list_hr(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return auth_service.list_hr_users(db)


@router.delete(
    "/users/{user_id}",
    response_model=MessageResponse,
)
def delete_hr(
    user_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    try:
        auth_service.delete_hr_user(db, user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    return MessageResponse(message="HR user deactivated successfully")


@router.get(
    "/settings",
    response_model=SettingsResponse,
)
def get_settings(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_staff),
):
    return settings_service.get_settings(db)


@router.put(
    "/settings",
    response_model=SettingsResponse,
)
def update_settings(
    data: SettingsUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    try:
        return settings_service.update_settings(db, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
