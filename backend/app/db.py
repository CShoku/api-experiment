# データベース接続とセッション管理を行うためのファイル
# SQLAlchemyを使用してPostgreSQLデータベースとの接続を設定

# SQLAlchemyの主要コンポーネントをインポート
# 設定ファイル（settings）からデータベースURLを取得
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .settings import settings

# データベースエンジンを作成
# settings.DATABASE_URLで指定されたデータベースに接続するエンジンを作成
# pool_pre_ping=True: 接続プールで接続の有効性を事前チェック
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# データベースセッションを作成するファクトリーの設定
# autocommit=False: 自動コミットを無効化
# autoflush=False: 自動フラッシュを無効化
# bind=engine: エンジンにバインド
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    """
    - すべてのデータベースモデルが継承するベースクラス
    - SQLAlchemy 2.0の新しいDeclarativeBaseを使用
    """
    pass

def get_db():
    """
    データベースセッションを取得するためのヘルパー関数
    FastAPIの依存性注入システムで使用される関数
    - リクエストごとに新しいデータベースセッションを作成
    - リクエスト終了時に自動的にセッションをクローズ
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
