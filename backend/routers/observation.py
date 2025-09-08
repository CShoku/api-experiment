# backend/routers/observation.py
"""
Observation Router
===================

観察データ（Observation）の作成・取得・解析ジョブ投入を行うAPIルータ。

- POST /observations              : 新しい観察データを作成
- POST /observations/{obs_id}/analyze : 指定した観察データを Cloud Tasks 経由で解析ジョブに投入
- GET  /observations/{obs_id}     : 観察データと解析結果を取得
"""

import os, json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from google.cloud import tasks_v2

from backend.apps.db import get_db
from backend.apps import models
from backend.schemas import (
    ObservationCreate,
    ObservationOut,
    DetectionOut,
    Candidate,
    TriviaOut,
    QuestionOut,
)
from backend.storage import public_url_from_key
from backend.deps import auth_optional

# ルータ定義
router = APIRouter(prefix="/observations", tags=["observations"])

# -------------------------
# Cloud Tasks の設定とクライアント
# -------------------------
_client = tasks_v2.CloudTasksClient()
_PROJECT = os.getenv("GCP_PROJECT")
_LOCATION = os.getenv("GCP_TASKS_LOCATION", "asia-northeast1")
_QUEUE = os.getenv("GCP_TASKS_QUEUE", "analyze")
_TARGET_URL = os.getenv("TASK_TARGET_URL")  # Cloud Run の /tasks/analyze URL
_TASK_SA = os.getenv("TASK_IAM_EMAIL")      # OIDC署名に使うサービスアカウント


def _enqueue_cloud_task(payload: dict):
    """
    Cloud Tasks に新しいタスクを投入するヘルパー関数。

    Args:
        payload (dict): タスクに渡すデータ（ここでは obs_id のみ）

    Returns:
        google.cloud.tasks_v2.types.Task: 作成されたタスクの情報
    """
    parent = _client.queue_path(_PROJECT, _LOCATION, _QUEUE)

    # Cloud Run の /tasks/analyze を叩く HTTP リクエストとしてタスクを構成
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": _TARGET_URL,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(payload).encode("utf-8"),
            # OIDC トークンで署名 → Cloud Run 側の認証必須設定でも通る
            "oidc_token": {"service_account_email": _TASK_SA},
        }
    }
    return _client.create_task(request={"parent": parent, "task": task})


# -------------------------
# エンドポイント定義
# -------------------------

@router.post("", response_model=dict)
def create_observation(
    payload: ObservationCreate,
    db: Session = Depends(get_db),
    user=Depends(auth_optional),
):
    """
    新しい観察データを登録する。

    - mediaUrl, 撮影日時, 緯度経度, exif情報を保存
    - ステータスは初期状態で "queued"

    Returns:
        dict: 作成された観察データのID
    """
    obs = models.Observation(
        user_id=None,               # 認証は後で対応予定なので現状は None
        media_url=payload.mediaUrl,
        taken_at=payload.takenAt,
        lat=payload.lat,
        lng=payload.lng,
        exif_json=payload.exif,
        status="queued",
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return {"id": obs.id}


@router.post("/{obs_id}/analyze", response_model=dict)
def enqueue_analyze(
    obs_id: int,
    db: Session = Depends(get_db),
    user=Depends(auth_optional),
):
    """
    指定した観察データを **Cloud Tasks 経由で解析ジョブに投入**する。

    - status を "processing" に更新
    - Cloud Tasks に `{ "obs_id": <id> }` のペイロードで投入
    - Cloud Tasks が Cloud Run の `/tasks/analyze` を叩き、非同期に解析実行する

    Args:
        obs_id (int): 観察データのID

    Returns:
        dict: {"status": "queued"}
    """
    obs = db.get(models.Observation, obs_id)
    if not obs:
        raise HTTPException(404, "observation not found")

    # status が既に processing でなければ更新
    if obs.status != "processing":
        obs.status = "processing"
        db.commit()

    # Cloud Tasks に投入
    _enqueue_cloud_task({"obs_id": obs_id})
    return {"status": "queued"}


@router.get("/{obs_id}", response_model=ObservationOut)
def get_observation(
    obs_id: int,
    db: Session = Depends(get_db),
    user=Depends(auth_optional),
):
    """
    指定した観察データと、その解析結果を返す。

    - Observation（撮影データ）
    - Detection（分類結果）
    - Trivia（雑学）
    - Question（問い）

    Args:
        obs_id (int): 観察データのID

    Returns:
        ObservationOut: 観察データと解析結果を含むレスポンス
    """
    obs = db.get(models.Observation, obs_id)
    if not obs:
        raise HTTPException(404, "not found")

    det = obs.detection
    detection = None
    trivia = None
    question = None

    if det:
        # 分類結果
        detection = DetectionOut(
            top_label=det.top_label,
            confidence=det.confidence,
            candidates=[Candidate(**c) for c in (det.label_candidates_json or [])],
            model_family=det.model_family,
        )
        # 雑学
        trivia = TriviaOut(
            title=det.trivia_title,
            body=det.trivia_body,
            source=det.trivia_source,
        )
        # 問い
        question = QuestionOut(
            body=det.question_body,
            audience=det.question_audience,
        )

    return ObservationOut(
        id=obs.id,
        status=obs.status,
        mediaUrl=obs.media_url,
        detection=detection,
        trivia=trivia,
        question=question,
    )
