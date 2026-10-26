# -*- coding: utf-8 -*-
"""管理者認証 API（パスワード保護用）。標準ライブラリで簡易 JWT を発行・検証。"""
import logging
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)

security = HTTPBearer()


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def create_access_token() -> str:
    payload = {
        "sub": "admin",
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def verify_token(token: str) -> bool:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            options={"require": ["sub", "exp"]},
        )
        return payload.get("sub") == "admin"
    except InvalidTokenError as e:
        logger.warning(f"Token verification failed: {e}")
        return False


@router.post("/login", response_model=LoginResponse)
async def login_admin(body: LoginRequest):
    # タイミング攻撃を防ぐため定数時間比較を使用
    if not secrets.compare_digest(body.password, settings.admin_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
    access_token = create_access_token()
    return LoginResponse(access_token=access_token)


def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if not verify_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return "admin"
