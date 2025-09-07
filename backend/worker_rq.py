import os, json
from redis import Redis
from rq import Worker, Queue, Connection
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app import models
from app.vlm_client import analyze_image

listen = ["analyze"]

def run_pipeline(obs_id: int):
    db: Session = SessionLocal()
    try:
        obs = db.get(models.Observation, obs_id)
        if not obs:
            return
        # 1) VLM呼び出し
        res = analyze_image(obs.media_url)
        # 2) 保存
        det = models.Detection(
            observation_id=obs.id,
            top_label=res.get("top_label"),
            confidence=res.get("confidence"),
            label_candidates_json=res.get("candidates"),
            model_family=res.get("model_family"),
            raw_json=res.get("raw"),
            trivia_title=(res.get("trivia") or {}).get("title"),
            trivia_body=(res.get("trivia") or {}).get("body"),
            trivia_source=(res.get("trivia") or {}).get("source"),
            question_body=(res.get("question") or {}).get("body"),
            question_audience=(res.get("question") or {}).get("audience"),
        )
        db.add(det)
        obs.status = "done"
        db.commit()
    except Exception as e:
        if obs:
            obs.status = "error"
            db.commit()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    conn = Redis.from_url(redis_url)
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
