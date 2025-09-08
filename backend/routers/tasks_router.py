"""
Tasks Router
============

Cloud Tasks が叩く **内部用エンドポイント** をまとめたルータ。

このルータは「外部ユーザーが直接使うAPI」ではなく、
- Cloud Tasks が OIDC 署名付きで Cloud Run を呼ぶ
- その HTTP リクエスト（/tasks/analyze）を受けて **解析処理を同期実行**
- 実行が終わったら 200 を返す（失敗時は例外→Cloud Tasks がリトライ）

という役割を担う。

セキュリティについて
--------------------
- **推奨**：Cloud Run サービスを「認証必須」にし、Cloud Tasks 側で `oidc_token` を設定。
  これにより、**入口で認証・認可が完結**し、アプリ内でのトークン検証は不要。
- ローカル開発や手動テスト用途で呼びたい場合は、`X-DEV-SECRET` ヘッダで
  簡易共有鍵のチェックを入れることもできる（下の `ALLOW_DEV_SECRET` を参照）。
"""

import os
from fastapi import APIRouter, Request, HTTPException, Header
from backend.apps.worker_core import run_pipeline

router = APIRouter(prefix="/tasks", tags=["tasks"])

# 開発時の**任意**の簡易ガード（本番では Cloud Run 側の認証必須で守る想定）
ALLOW_DEV_SECRET = os.getenv("TASKS_DEV_SECRET")  # 例: "local-ok"（未設定ならチェック無効）


@router.post("/analyze")
async def tasks_analyze(
    request: Request,
    x_dev_secret: str | None = Header(default=None, alias="X-DEV-SECRET"),
):
    """
    Cloud Tasks からキュー投入された **解析ジョブ** を実行するエンドポイント。

    受け取るボディ:
        {
          "obs_id": <int>  # 解析対象の Observation ID
        }

    処理の流れ:
        1) （開発時のみ）任意の共有鍵ヘッダ `X-DEV-SECRET` をチェック
        2) JSON ボディから `obs_id` を取り出す
        3) `worker_core.run_pipeline(obs_id)` を **同期で実行**
        4) 成功なら {"ok": True} を返す（失敗は例外 → Cloud Tasks 再試行）

    Notes:
        - 本エンドポイントは **同期実行**。Cloud Run のリクエストタイムアウト内で完結する想定。
        - 失敗時は例外をそのまま投げることで、Cloud Tasks のリトライポリシーに委ねる。
    """
    # （任意）ローカル/手動テスト用の簡易共有鍵チェック
    if ALLOW_DEV_SECRET:
        if x_dev_secret != ALLOW_DEV_SECRET:
            raise HTTPException(status_code=401, detail="unauthorized (dev secret mismatch)")

    # JSON を取得
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid JSON")

    # obs_id を取り出して検証
    try:
        obs_id = int(body["obs_id"])
    except Exception:
        raise HTTPException(status_code=400, detail="`obs_id` is required and must be int")

    # 解析本体を実行（例外は上位に投げる → Cloud Tasks が再試行）
    run_pipeline(obs_id)

    return {"ok": True}
