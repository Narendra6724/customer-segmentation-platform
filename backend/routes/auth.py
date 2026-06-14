"""
Auth & Admin Routes — login, user management.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.services import user_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    id: int
    email: str
    role: str


class CreateUserRequest(BaseModel):
    email: str
    password: str
    role: str = "member"


class ChangePasswordRequest(BaseModel):
    email: str
    new_password: str


class UserOut(BaseModel):
    id: int
    email: str
    role: str
    created_at: str | None


class MessageResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_admin(x_user_role: str = Header(default="")):
    """Dependency that checks the X-User-Role header equals 'admin'."""
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/auth/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a user and return their profile."""
    user = user_service.authenticate(db, req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return LoginResponse(**user)


@router.get("/admin/users", response_model=list[UserOut], dependencies=[Depends(_require_admin)])
def list_users(db: Session = Depends(get_db)):
    """List all registered users (admin only)."""
    return user_service.list_users(db)


@router.post("/admin/users", response_model=UserOut, dependencies=[Depends(_require_admin)])
def create_user(req: CreateUserRequest, db: Session = Depends(get_db)):
    """Create a new user (admin only)."""
    try:
        return user_service.create_user(db, req.email, req.password, req.role)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/admin/users/password", response_model=MessageResponse, dependencies=[Depends(_require_admin)])
def change_password(req: ChangePasswordRequest, db: Session = Depends(get_db)):
    """Change a user's password (admin only)."""
    try:
        user_service.change_password(db, req.email, req.new_password)
        return MessageResponse(message=f"Password updated for {req.email}.")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/admin/users/{email}", response_model=MessageResponse, dependencies=[Depends(_require_admin)])
def delete_user(email: str, db: Session = Depends(get_db)):
    """Delete a user (admin only). Cannot delete yourself."""
    if user_service.delete_user(db, email):
        return MessageResponse(message=f"User '{email}' deleted.")
    raise HTTPException(status_code=404, detail=f"User '{email}' not found.")
