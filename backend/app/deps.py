from fastapi import Depends, Header, HTTPException
from .settings import settings

def auth_optional(authorization: str | None = Header(default=None)):
    # MVPでは省略可能。必要ならJWT検証をここに。
    return {"user_id": None}
