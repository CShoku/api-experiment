from fastapi import APIRouter, Depends
from ..schemas import UploadInitReq, UploadInitRes
from ..storage import create_presigned_put, public_url_from_key
from ..deps import auth_optional

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/init", response_model=UploadInitRes)
def init_upload(req: UploadInitReq, user=Depends(auth_optional)):
    """
    ファイルアップロード用の署名付きURLを初期化する
    
    Args:
        req: アップロード初期化リクエスト（拡張子とMIMEタイプを含む）
        user: 認証情報（現在は未使用）
        
    Returns:
        UploadInitRes: 署名付きURL、オブジェクトキー、公開URLを含むレスポンス
    """
    url, key = create_presigned_put(req.ext, req.mime)
    public_url = public_url_from_key(key)
    return UploadInitRes(url=url, object_key=key, public_url=public_url)

