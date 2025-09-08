"""
Worker Core
===========

解析ジョブ（画像 → ラベル候補/雑学/問いの生成）の**本体ロジック**を集約したモジュール。
Cloud Tasks（/tasks/analyze）や、将来の別実装（Lambda/Celery/RQ）からも
**同じ関数 run_pipeline(obs_id)** を呼び出せるようにしておくのが目的。

責務:
- Observation を DB から取得
- VLM クライアント（vlm_client.analyze_image）を呼んで解析
- Detection レコードを作成して保存
- Observation.status を "done" / "error" に更新

ポイント:
- 解析は **同期実行**（呼び出し元が非同期キューを担う）
- 例外は**握りつぶさずに再送**（Cloud Tasks のリトライ等に任せる）
- 将来の冪等性（重複投入）に備えて Upsert 化する余地をコメントで示す
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from backend.apps.db import SessionLocal
from backend.apps import models
from backend.apps.vlm_client import analyze_image


def _save_detection(db: Session, obs: models.Observation, res: Dict[str, Any]) -> None:
    """
    VLM の応答 `res` を DB の Detection レコードに反映して保存する。

    ここでは **新規作成** 想定。重複実行がありうる運用では、以下のどちらかを推奨:
      - Detection(observation_id) に **一意制約**を張って Upsert（衝突時は上書き）
      - 既存があれば **更新**（db.merge / 手動コピー）する

    Args:
        db (Session): DB セッション
        obs (models.Observation): 対象 Observation
        res (dict): VLM からの解析結果（ダミー/本番いずれも可）
    """
    candidates = res.get("candidates") or []
    trivia = res.get("trivia") or {}
    question = res.get("question") or {}

    det = models.Detection(
        observation_id=obs.id,
        top_label=res.get("top_label"),
        confidence=res.get("confidence"),
        label_candidates_json=candidates,        # JSON カラム
        model_family=res.get("model_family"),
        raw_json=res.get("raw") or res,          # 生の応答を最小限保持（デバッグ/将来改善用）
        trivia_title=trivia.get("title"),
        trivia_body=trivia.get("body"),
        trivia_source=trivia.get("source"),
        question_body=question.get("body"),
        question_audience=question.get("audience"),
    )
    db.add(det)


def run_pipeline(obs_id: int) -> None:
    """
    観察データ `obs_id` について **解析→保存→ステータス更新** を行う同期処理。

    呼び出し元（/tasks/analyze など）はこの関数を**1回のジョブ処理**として実行すればOK。

    フロー:
        1) Observation を取得（存在しなければ何もせず終了）
        2) `vlm_client.analyze_image(media_url)` を呼ぶ
        3) Detection を作成して保存
        4) Observation.status を "done" にして commit
       [例外時] Observation.status を "error" にし、例外は**再送のため raise**

    Note:
        - VLM クライアントは現状ダミーでもOK（後で差し替え可能）
        - 失敗のハンドリングは「Cloud Tasks / 呼び出し側のリトライ」に任せる
    """
    db: Session = SessionLocal()
    obs: Optional[models.Observation] = None
    try:
        # 1) 対象の観察データを取得
        obs = db.get(models.Observation, obs_id)
        if not obs:
            # 既に削除等されていた場合は何もしない
            return

        # 2) 画像URLを渡して解析（ダミー/本番いずれの実装でも同じ呼び口）
        res = analyze_image(obs.media_url)

        # 3) Detection を保存
        _save_detection(db, obs, res)

        # 4) ステータス更新 → commit
        obs.status = "done"
        db.commit()

    except Exception:
        # 例外時はステータスを error に倒してから再送のために再raise
        try:
            if obs:
                obs.status = "error"
                db.commit()
        except Exception:
            # 二次障害は握りつぶして元の例外を優先
            pass
        raise
    finally:
        db.close()
