# api-experiment

使い方（ローカル・予選想定）

.env を作成（.env.example をコピーして値を調整）

MinIO のバケット media を作成（初回は http://localhost:9001
 にアクセス）

docker-compose up --build

POST /upload/init → 署名URLで直PUT → POST /observations → POST /observations/{id}/analyze

GET /observations/{id} で結果を取得（ダミーVLMでも値が入ります）

✅ 補足

GCSに切替：storage.py の create_presigned_put を google-cloud-storage 実装に置換

本物のVLM接続：vlm_client.py で OpenAI/Gemini/Anthropic を実装（image_url で投げる）

スキーマ拡張：embeddings テーブルや pgvector を後付け可

認証：deps.auth_optional をJWT検証に差し替え