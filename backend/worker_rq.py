import os
import time
import json
import traceback
from typing import Any, Dict, List

from redis import Redis
from rq import Worker, Queue, Connection
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app import models
from app.vlm_client import analyze_image

# RQのキュー名（enqueue側と一致させる）
LISTEN_QUEUES = ["analyze"]


def _ensure_list(x: Any) -> List:
    """
    入力値をリストに変換するヘルパー関数
    
    Args:
        x: 変換対象の値（None、リスト、その他の型）
        
    Returns:
        List: 入力値がNoneの場合は空リスト、リストの場合はそのまま、その他の場合は単一要素のリスト
    """
    if x is None:
        return []
    if isinstance(x, list):
        return x
    # dict等が来ても落ちずにログだけ残す
    return [x]


def run_pipeline(obs_id: int):
    """
    観察記録の画像解析パイプラインを実行する
    
    RQワーカーから呼び出される関数で、指定された観察記録の画像を解析し、
    検出結果、トリビア、質問を生成してデータベースに保存する。
    
    Args:
        obs_id: 解析対象の観察記録ID
        
    Raises:
        Exception: 解析処理中にエラーが発生した場合
    """
    db: Session = SessionLocal()
    try:
        obs = db.get(models.Observation, obs_id)
        if not obs:
            return
        # 解析中表示のため
        obs.status = "processing"
        db.commit()

        res = analyze_image(obs.media_url)  # ← ここはダミーのままでOK

        det = models.Detection(
            observation_id=obs.id,
            top_label=res.get("top_label"),
            confidence=res.get("confidence"),
            label_candidates_json=res.get("candidates") or [],
            model_family=res.get("model_family"),
            raw_json=res.get("raw") or res,
            trivia_title=(res.get("trivia") or {}).get("title"),
            trivia_body=(res.get("trivia") or {}).get("body"),
            trivia_source=(res.get("trivia") or {}).get("source"),
            question_body=(res.get("question") or {}).get("body"),
            question_audience=(res.get("question") or {}).get("audience"),
        )
        db.add(det)
        obs.status = "done"
        db.commit()
    except Exception:
        if obs:
            obs.status = "error"
            db.commit()
        raise
    finally:
        db.close()
