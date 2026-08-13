from dataclasses import asdict

from fastapi import APIRouter, Cookie, HTTPException, Response, status
from pydantic import BaseModel, Field

from backend.config import (
    SESSION_COOKIE_NAME,
    SESSION_COOKIE_SECURE,
    SESSION_DURATION_DAYS,
)
from backend.services.auth_service import (
    AuthenticationError,
    AuthService,
    EmailAlreadyRegisteredError,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)

auth_service = AuthService()


class CredentialsRequest(BaseModel):
    email: str = Field(..., max_length=254)
    password: str = Field(..., min_length=1, max_length=128)
    time_zone: str = Field(default="Asia/Shanghai", max_length=64)


def _set_session_cookie(response: Response, session_token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=SESSION_DURATION_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


def require_current_user(
    session_token: str | None = Cookie(
        default=None,
        alias=SESSION_COOKIE_NAME,
    ),
):
    """Require a valid browser session for a protected API route."""
    try:
        return auth_service.get_user_for_session_token(session_token)
    except AuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
        ) from error


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    request: CredentialsRequest,
    response: Response,
) -> dict:
    try:
        user = auth_service.register(
            request.email,
            request.password,
            request.time_zone,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该邮箱已注册，请直接登录",
        ) from error

    session_token = auth_service.create_session(
        user.id,
        SESSION_DURATION_DAYS,
    )
    _set_session_cookie(response, session_token)

    return {
        "success": True,
        "data": asdict(user),
        "message": "注册成功，已登录",
    }


@router.post("/login")
def login(
    request: CredentialsRequest,
    response: Response,
) -> dict:
    try:
        user = auth_service.login(request.email, request.password)
    except AuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码不正确",
        ) from error

    session_token = auth_service.create_session(
        user.id,
        SESSION_DURATION_DAYS,
    )
    _set_session_cookie(response, session_token)

    return {
        "success": True,
        "data": asdict(user),
        "message": "登录成功",
    }


@router.post("/logout")
def logout(
    response: Response,
    session_token: str | None = Cookie(
        default=None,
        alias=SESSION_COOKIE_NAME,
    ),
) -> dict:
    auth_service.revoke_session(session_token)
    _clear_session_cookie(response)

    return {
        "success": True,
        "data": None,
        "message": "已退出登录",
    }


@router.get("/me")
def get_current_user(
    session_token: str | None = Cookie(
        default=None,
        alias=SESSION_COOKIE_NAME,
    ),
) -> dict:
    user = require_current_user(session_token)

    return {
        "success": True,
        "data": asdict(user),
        "message": "",
    }
