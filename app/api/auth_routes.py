from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel

from app.core.auth import clear_auth_cookie, get_authenticated_user, set_auth_cookie, validate_credentials
from config import AUTH_ENABLED, AUTH_USERNAME


router = APIRouter(prefix="/api/auth", tags=["Auth"])


class LoginBody(BaseModel):
    username: str
    password: str


@router.get("/me")
async def auth_me(request: Request):
    user = get_authenticated_user(request)
    return {
        "enabled": AUTH_ENABLED,
        "authenticated": bool(user),
        "username": user["username"] if user else None,
        "default_username": AUTH_USERNAME if AUTH_ENABLED else None,
    }


@router.post("/login")
async def auth_login(body: LoginBody, response: Response):
    if not AUTH_ENABLED:
        response.status_code = status.HTTP_204_NO_CONTENT
        return

    if not validate_credentials(body.username, body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Basic"},
        )

    set_auth_cookie(response, body.username)
    return {
        "authenticated": True,
        "username": body.username,
    }


@router.post("/logout")
async def auth_logout(response: Response):
    clear_auth_cookie(response)
    return {"authenticated": False}
