from fastapi import Depends, Header, HTTPException
from .settings import settings

def auth_optional(authorization: str | None = Header(default=None)):
    """
    認証を省略可能にする依存性関数
    
    MVPでは認証を省略可能とし、常にuser_id=Noneを返す。
    本格運用時はJWT検証を実装する。
    
    Args:
        authorization: Authorizationヘッダーの値（現在は未使用）
        
    Returns:
        dict: {"user_id": None} の辞書を返す
    """
    # MVPでは省略可能。必要ならJWT検証をここに。
    return {"user_id": None}
