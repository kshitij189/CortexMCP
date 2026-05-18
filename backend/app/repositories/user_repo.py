"""Data access layer for user operations."""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.utils.security import hash_password


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Fetch a user by email address."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Fetch a user by username."""
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Fetch a user by UUID."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, email: str, username: str, password: str) -> User:
    """Create a new user with hashed password."""
    user = User(
        email=email,
        username=username,
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
