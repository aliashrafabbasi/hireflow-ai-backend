from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.repositories.user import (
    create_user,
    get_user_by_email
)
from app.schemas.user import UserCreate


def register_user(
    db: Session,
    user_data: UserCreate
):
    existing_user = get_user_by_email(
        db,
        user_data.email
    )

    if existing_user:
        raise ValueError("Email already registered")

    hashed_password = hash_password(
        user_data.password
    )

    user = create_user(
        db,
        user_data,
        hashed_password
    )

    return user


from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)


def login_user(
    db: Session,
    email: str,
    password: str,
) -> str:
    user = get_user_by_email(
        db,
        email,
    )

    if not user:
        raise ValueError("Invalid email or password")

    if not verify_password(
        password,
        user.password_hash,
    ):
        raise ValueError("Invalid email or password")

    return create_access_token(user.email)