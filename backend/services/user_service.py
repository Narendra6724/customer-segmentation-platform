"""
User Service — authentication, user CRUD, and initial seeding.
"""

import hashlib
from sqlalchemy.orm import Session
from backend.models.user import User
from backend.database.db import SessionLocal


def _hash_password(password: str) -> str:
    """SHA-256 hash for password storage."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Initial seed data
# ---------------------------------------------------------------------------
SEED_USERS = [
    {"email": "gnarendra_csd236724@mgit.ac.in", "password": "12345678", "role": "admin"},
    {"email": "bsaicharanreddy_csd236715@mgit.ac.in", "password": "12345678", "role": "member"},
    {"email": "irfanbabu@mgit.ac.in", "password": "12345678", "role": "member"},
    {"email": "aswapna_cse@mgit.ac.in", "password": "12345678", "role": "member"},
    {"email": "rpawar_csd236749@mgit.ac.in", "password": "12345678", "role": "member"},
]


def seed_initial_users():
    """Insert seed users if they don't already exist. Called on app startup."""
    db: Session = SessionLocal()
    try:
        for u in SEED_USERS:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                db.add(User(
                    email=u["email"],
                    password_hash=_hash_password(u["password"]),
                    role=u["role"],
                ))
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def authenticate(db: Session, email: str, password: str) -> dict | None:
    """Validate credentials. Returns user dict or None."""
    user = db.query(User).filter(User.email == email).first()
    if user and user.password_hash == _hash_password(password):
        return user.to_dict()
    return None


# ---------------------------------------------------------------------------
# Admin CRUD
# ---------------------------------------------------------------------------

def create_user(db: Session, email: str, password: str, role: str = "member") -> dict:
    """Create a new user. Raises ValueError if email already exists."""
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise ValueError(f"User with email '{email}' already exists.")
    user = User(
        email=email,
        password_hash=_hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.to_dict()


def change_password(db: Session, email: str, new_password: str) -> dict:
    """Change a user's password. Raises ValueError if user not found."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError(f"User '{email}' not found.")
    user.password_hash = _hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user.to_dict()


def list_users(db: Session) -> list[dict]:
    """Return all registered users."""
    rows = db.query(User).order_by(User.id).all()
    return [row.to_dict() for row in rows]


def delete_user(db: Session, email: str) -> bool:
    """Delete a user by email. Returns True if deleted, False if not found."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True
