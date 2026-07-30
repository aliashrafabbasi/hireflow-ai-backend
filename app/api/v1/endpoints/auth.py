from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    LoginResponse,
)
from app.services.auth import (
    register_admin,
    login_user,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register-admin",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_admin_endpoint(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    try:
        return register_admin(db, user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    user: UserLogin,
    db: Session = Depends(get_db),
):
    try:
        return login_user(
            db,
            user.email,
            user.password,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
