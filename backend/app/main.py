from fastapi import FastAPI
from .db import Base, engine
from .routers import observations, upload

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Nature MVP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 必要に応じて本番で絞る
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Base.metadata.create_all(bind=engine)

app.include_router(upload.router)
app.include_router(observations.router)

@app.get("/health")
def health():
    """
    ヘルスチェック用のエンドポイント
    
    Returns:
        dict: {"ok": True} のレスポンスを返す
    """
    return {"ok": True}
