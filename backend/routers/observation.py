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
    """
    新しい観察記録を作成する
    
    Args:
        payload: 観察記録の作成データ（メディアURL、撮影日時、位置情報、EXIF等）
        db: データベースセッション
        user: 認証情報（現在は未使用）
        
    Returns:
        dict: 作成された観察記録のIDを含む辞書
    """
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
    """
    観察記録の画像解析を開始する
    
    Args:
        obs_id: 解析対象の観察記録ID
        db: データベースセッション
        user: 認証情報（現在は未使用）
        
    Returns:
        dict: バックグラウンドジョブのIDを含む辞書
        
    Raises:
        HTTPException: 観察記録が見つからない場合（404エラー）
    """
    obs = db.get(models.Observation, obs_id)
    if not obs:
        raise HTTPException(404, "observation not found")
    # 多重実行抑止は適宜（ここでは簡略）
    job = queue.enqueue("worker_rq.run_pipeline", obs_id, job_timeout=600)
    obs.status = "processing"; db.commit()
    return {"jobId": job.id}

@router.get("/{obs_id}", response_model=ObservationOut)
def get_observation(obs_id: int, db: Session = Depends(get_db), user=Depends(auth_optional)):
    """
    観察記録の詳細情報を取得する
    
    Args:
        obs_id: 取得対象の観察記録ID
        db: データベースセッション
        user: 認証情報（現在は未使用）
        
    Returns:
        ObservationOut: 観察記録の詳細情報（検出結果、トリビア、質問を含む）
        
    Raises:
        HTTPException: 観察記録が見つからない場合（404エラー）
    """
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
