from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.repositories import user as user_repository
from app.schemas.user import UserCreate


def register_admin(
    db: Session,
    user_data: UserCreate,
):
    if user_repository.admin_exists(db):
        raise ValueError("Admin already exists")

    existing_user = user_repository.get_user_by_email(
        db,
        user_data.email,
    )
    if existing_user:
        raise ValueError("Email already registered")

    return user_repository.create_user(
        db,
        user_data,
        hash_password(user_data.password),
        role="admin",
    )


def create_hr_user(
    db: Session,
    user_data: UserCreate,
):
    existing_user = user_repository.get_user_by_email(
        db,
        user_data.email,
    )
    if existing_user:
        raise ValueError("Email already registered")

    return user_repository.create_user(
        db,
        user_data,
        hash_password(user_data.password),
        role="hr",
    )


def register_career_user(
    db: Session,
    user_data: UserCreate,
):
    """Create a public career-portal account with the user role."""
    existing_user = user_repository.get_user_by_email(
        db,
        user_data.email,
    )
    if existing_user:
        raise ValueError("Email already registered")

    return user_repository.create_user(
        db,
        user_data,
        hash_password(user_data.password),
        role="user",
    )


def list_hr_users(db: Session):
    return user_repository.get_hr_users(db)


def list_career_users(db: Session):
    return user_repository.get_career_users(db)


def get_career_user(
    db: Session,
    user_id,
):
    user = user_repository.get_user_by_id(db, user_id)
    if not user or user.role != "user":
        raise ValueError("Career user not found")
    return user


def delete_hr_user(
    db: Session,
    user_id,
):
    user = user_repository.get_user_by_id(db, user_id)

    if not user:
        raise ValueError("User not found")

    if user.role != "hr":
        raise PermissionError("Only HR users can be deleted")

    if not user.is_active:
        raise ValueError("HR user is already deactivated")

    return user_repository.soft_delete_user(db, user)


def delete_career_user(
    db: Session,
    user_id,
):
    user = get_career_user(db, user_id)

    if not user.is_active:
        raise ValueError("Career user is already deactivated")

    return user_repository.soft_delete_user(db, user)


def login_user(
    db: Session,
    email: str,
    password: str,
):
    user = user_repository.get_user_by_email(db, email)

    if not user:
        raise ValueError("Invalid email or password")

    if not user.is_active:
        raise ValueError("Account is inactive")

    if not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")

    access_token = create_access_token(user.email)

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }
