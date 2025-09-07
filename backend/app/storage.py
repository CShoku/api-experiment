import boto3, uuid
from .settings import settings

s3 = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT_URL,
    aws_access_key_id=settings.S3_ACCESS_KEY_ID,
    aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
    region_name=settings.S3_REGION,
)

def create_presigned_put(ext: str, mime: str) -> tuple[str, str]:
    key = f"obs/{uuid.uuid4()}{ext}"
    url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key, "ContentType": mime},
        ExpiresIn=settings.PRESIGNED_TTL_SECONDS,
    )
    return url, key

def public_url_from_key(key: str) -> str:
    # ローカルMinIO用（本番はCDNドメインを環境変数で）
    base = settings.PUBLIC_CDN_BASE or f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET}"
    return f"{base}/{key}"

# GCSでやる場合の差し替えポイント（例）:
# - google-cloud-storage を使って signed_url を発行
