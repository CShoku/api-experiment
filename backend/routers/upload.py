from fastapi import APIRouter, Depends
from ..schemas import UploadInitReq, UploadInitRes
from ..storage import create_presigned_put
from ..deps import auth_optional

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/init", response_model=UploadInitRes)
def init_upload(req: UploadInitReq, user=Depends(auth_optional)):
    url, key = create_presigned_put(req.ext, req.mime)
    return UploadInitRes(url=url, object_key=key)
