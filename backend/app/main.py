from fastapi import FastAPI
from .db import Base, engine
from .routers import observations, upload

app = FastAPI(title="TicketDive MVP API")  # ちけっとだいぶ=TicketDive

Base.metadata.create_all(bind=engine)

app.include_router(upload.router)
app.include_router(observations.router)

@app.get("/health")
def health():
    return {"ok": True}
