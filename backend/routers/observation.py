from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models
from ..schemas import ObservationCreate, ObservationOut, DetectionOut, Candidate, TriviaOut, QuestionOut
from ..storage import public_url_from_key
from ..deps import auth_optional
import os, json
from redis import Redis
from rq import Queue

router = APIRouter(prefix="/observations", tags=["observations"])
redis_conn = Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
queue = Queue("analyze", connection=redis_conn)

@router.post("", response_model=dict)
def create_observation(payload: ObservationCreate, db: Session = Depends(get_db), user=Depends(auth_optional)):
    obs = models.Observation(
        user_id=None,
        media_url=payload.mediaUrl,
        taken_at=payload.takenAt,
        lat=payload.lat, lng=payload.lng,
        exif_json=payload.exif,
        status="queued",
    )
    db.add(obs); db.commit(); db.refresh(obs)
    return {"id": obs.id}

@router.post("/{obs_id}/analyze", response_model=dict)
def analyze(obs_id: int, db: Session = Depends(get_db), user=Depends(auth_optional)):
    obs = db.get(models.Observation, obs_id)
    if not obs:
        raise HTTPException(404, "observation not found")
    # 多重実行抑止は適宜（ここでは簡略）
    job = queue.enqueue("worker_rq.run_pipeline", obs_id, job_timeout=600)
    obs.status = "processing"; db.commit()
    return {"jobId": job.id}

@router.get("/{obs_id}", response_model=ObservationOut)
def get_observation(obs_id: int, db: Session = Depends(get_db), user=Depends(auth_optional)):
    obs = db.get(models.Observation, obs_id)
    if not obs:
        raise HTTPException(404, "not found")
    det = obs.detection
    detection = None; trivia=None; question=None
    if det:
        detection = DetectionOut(
            top_label=det.top_label,
            confidence=det.confidence,
            candidates=[Candidate(**c) for c in (det.label_candidates_json or [])],
            model_family=det.model_family,
        )
        trivia = TriviaOut(title=det.trivia_title, body=det.trivia_body, source=det.trivia_source)
        question = QuestionOut(body=det.question_body, audience=det.question_audience)
    return ObservationOut(
        id=obs.id,
        status=obs.status,
        mediaUrl=obs.media_url,
        detection=detection,
        trivia=trivia,
        question=question,
    )
