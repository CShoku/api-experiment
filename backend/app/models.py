from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from .db import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    handle: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Observation(Base):
    __tablename__ = "observations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    media_url: Mapped[str] = mapped_column(Text, nullable=False)  # s3:// or https
    thumb_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    taken_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    geohash: Mapped[str | None] = mapped_column(String(16), nullable=True)
    exif_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="queued")  # queued|processing|done|error
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    detection = relationship("Detection", back_populates="observation", uselist=False)

class Detection(Base):
    __tablename__ = "detections"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    observation_id: Mapped[int] = mapped_column(Integer, ForeignKey("observations.id"), index=True)
    top_label: Mapped[str | None] = mapped_column(String(128))
    confidence: Mapped[float | None] = mapped_column(Float)
    label_candidates_json: Mapped[dict | None] = mapped_column(JSON)
    model_family: Mapped[str | None] = mapped_column(String(64))
    raw_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    trivia_title: Mapped[str | None] = mapped_column(String(128))
    trivia_body: Mapped[str | None] = mapped_column(Text)
    trivia_source: Mapped[str | None] = mapped_column(String(512))
    question_body: Mapped[str | None] = mapped_column(String(64))
    question_audience: Mapped[str | None] = mapped_column(String(16))

    observation = relationship("Observation", back_populates="detection")
