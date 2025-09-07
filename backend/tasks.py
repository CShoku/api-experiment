import os
from celery import Celery
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app import models
from app.vlm_client import analyze_image

broker_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery("tasks", broker=broker_url, backend=broker_url)

@celery_app.task(name="analyze_observation", bind=True, max_retries=3, default_retry_delay=5)
def analyze_observation(self, obs_id: int):
    db: Session = SessionLocal()
    try:
        obs = db.get(models.Observation, obs_id)
        if not obs: return
        res = analyze_image(obs.media_url)
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
        db.add(det); obs.status="done"; db.commit()
    except Exception as e:
        if obs:
            obs.status="error"; db.commit()
        raise
    finally:
        db.close()
