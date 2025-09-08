from fastapi import FastAPI
from .db import Base, engine
from backend.routers.upload import router as upload_router
from backend.routers.observation import router as observation_router
from backend.routers.tasks_router import router as tasks_router

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

app.include_router(upload_router, prefix="/upload")
app.include_router(observation_router)
app.include_router(tasks_router)

@app.get("/health")
def health():
    """
    ヘルスチェック用のエンドポイント
    
    Returns:
        dict: {"ok": True} のレスポンスを返す
    """
    return {"ok": True}
