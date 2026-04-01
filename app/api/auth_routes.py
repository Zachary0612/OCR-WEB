from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    clear_auth_cookie,
    get_authenticated_user,
    hash_password,
    require_admin,
    set_auth_cookie,
    validate_credentials,
    verify_password,
)
from app.db.database import get_db
from app.db.models import AppUser
from config import AUTH_ENABLED, AUTH_USERNAME


router = APIRouter(prefix="/api/auth", tags=["Auth"])


class LoginBody(BaseModel):
    username: str
    password: str


class RegisterBody(BaseModel):
    username: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=6, max_length=200)


class AuthPendingUserOut(BaseModel):
    id: int
    username: str
    status: str
    created_at: str | None = None


def _require_feature_enabled() -> None:
    if AUTH_ENABLED:
        return
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Auth is disabled.")


@router.get("/me")
async def auth_me(request: Request):
    user = get_authenticated_user(request)
    return {
        "enabled": AUTH_ENABLED,
        "authenticated": bool(user),
        "username": user["username"] if user else None,
        "is_admin": bool(user.get("is_admin")) if user else False,
        "user_status": user.get("user_status") if user else None,
        "default_username": AUTH_USERNAME if AUTH_ENABLED else None,
    }


@router.post("/register")
async def auth_register(body: RegisterBody, db: AsyncSession = Depends(get_db)):
    _require_feature_enabled()
    username = body.username.strip()
    if not username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username cannot be empty.")
    if username.lower() == AUTH_USERNAME.lower():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This username is reserved.")

    existing = (
        await db.execute(select(AppUser).where(AppUser.username == username))
    ).scalar_one_or_none()
    if existing:
        if existing.status == "pending":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This account is pending approval.")
        if existing.status == "active":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This username is already in use.")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This account has been rejected.")

    user = AppUser(
        username=username,
        password_hash=hash_password(body.password),
        status="pending",
        is_admin=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {
        "registered": True,
        "status": "pending",
        "message": "Registration submitted. Please wait for administrator approval.",
    }


@router.post("/login")
async def auth_login(body: LoginBody, response: Response, db: AsyncSession = Depends(get_db)):
    if not AUTH_ENABLED:
        response.status_code = status.HTTP_204_NO_CONTENT
        return

    username = body.username.strip()
    password = body.password or ""
    if not username or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username and password are required.")

    # Environment super admin keeps highest priority for emergency access.
    if validate_credentials(username, password):
        set_auth_cookie(response, username, is_admin=True, user_status="active")
        return {
            "authenticated": True,
            "username": username,
            "is_admin": True,
            "user_status": "active",
        }

    user = (
        await db.execute(select(AppUser).where(AppUser.username == username))
    ).scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Basic"},
        )

    if user.status == "pending":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account pending approval. Please contact administrator.",
        )
    if user.status == "rejected":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account rejected. Please contact administrator.",
        )
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is unavailable.")

    set_auth_cookie(
        response,
        user.username,
        user_id=user.id,
        is_admin=bool(user.is_admin),
        user_status=user.status,
    )
    return {
        "authenticated": True,
        "username": user.username,
        "is_admin": bool(user.is_admin),
        "user_status": user.status,
    }


@router.post("/logout")
async def auth_logout(response: Response):
    clear_auth_cookie(response)
    return {"authenticated": False}


@router.get("/pending-users")
async def auth_pending_users(request: Request, db: AsyncSession = Depends(get_db)):
    _require_feature_enabled()
    require_admin(request)

    pending_users = (
        await db.execute(
            select(AppUser).where(AppUser.status == "pending").order_by(AppUser.created_at.desc())
        )
    ).scalars().all()
    return {
        "items": [
            AuthPendingUserOut(
                id=user.id,
                username=user.username,
                status=user.status,
                created_at=user.created_at.isoformat() if user.created_at else None,
            ).model_dump(mode="json")
            for user in pending_users
        ]
    }


@router.post("/users/{user_id}/approve")
async def auth_approve_user(user_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    _require_feature_enabled()
    require_admin(request)

    user = await db.get(AppUser, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user.status = "active"
    await db.commit()
    return {"id": user.id, "username": user.username, "status": user.status}


@router.post("/users/{user_id}/reject")
async def auth_reject_user(user_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    _require_feature_enabled()
    require_admin(request)

    user = await db.get(AppUser, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user.status = "rejected"
    await db.commit()
    return {"id": user.id, "username": user.username, "status": user.status}
