# -*- coding: utf-8 -*-
"""管理者認証 API（パスワード保護用）。標準ライブラリで簡易 JWT を発行・検証。"""
import base64
import json
import hmac
import hashlib
from datetime import datetime, timedelta
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(b64: str) -> bytes:
    pad = b"=" * (4 - len(b64) % 4)
    return base64.urlsafe_b64decode((b64 + pad).encode("ascii"))


def create_access_token() -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    exp = int(
        (datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)).timestamp()
    )
    payload = {"sub": "admin", "exp": exp}

    header_b64 = _b64url_encode(json.dumps(header).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload).encode("utf-8"))

    msg = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(
        settings.jwt_secret.encode("utf-8"), msg, hashlib.sha256
    ).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def verify_token(token: str) -> bool:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return False
        header_b64, payload_b64, sig_b64 = parts

        msg = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = hmac.new(
            settings.jwt_secret.encode("utf-8"), msg, hashlib.sha256
        ).digest()

        if not hmac.compare_digest(_b64url_decode(sig_b64), expected_sig):
            return False

        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        if payload.get("sub") != "admin":
            return False
        if payload.get("exp", 0) < int(datetime.utcnow().timestamp()):
            return False
        return True
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        return False


@router.post("/login", response_model=LoginResponse)
async def login_admin(body: LoginRequest):
    if body.password != settings.admin_password:
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
