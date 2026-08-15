from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate


def get_user_by_email(
    db: Session,
    email: str,
):
    return (
        db.query(User)
        .filter(User.email == email)
        .first()
    )


def get_user_by_id(
    db: Session,
    user_id: UUID,
):
    return (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )


def admin_exists(db: Session) -> bool:
    return (
        db.query(User)
        .filter(User.role == "admin")
        .first()
        is not None
    )


def get_hr_users(db: Session) -> list[User]:
    return (
        db.query(User)
        .filter(
            User.role == "hr",
            User.is_active.is_(True),
        )
        .order_by(User.created_at.desc())
        .all()
    )


def get_career_users(db: Session) -> list[User]:
    """Return all career accounts, including deactivated accounts, for admins."""
    return (
        db.query(User)
        .filter(User.role == "user")
        .order_by(User.created_at.desc())
        .all()
    )


def create_user(
    db: Session,
    user_data: UserCreate,
    hashed_password: str,
    role: str,
):
    user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=hashed_password,
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def soft_delete_user(
    db: Session,
    user: User,
):
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user
