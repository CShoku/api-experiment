from pydantic import BaseModel, Field
from typing import Optional, List, Any

class UploadInitReq(BaseModel):
    ext: str = ".jpg"
    mime: str = "image/jpeg"

class UploadInitRes(BaseModel):
    url: str
    object_key: str
    public_url: str

class ObservationCreate(BaseModel):
    mediaUrl: str
    takenAt: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    exif: Optional[dict] = None

class Candidate(BaseModel):
    ja: str
    en: Optional[str] = None
    sci: Optional[str] = None
    score: float

class DetectionOut(BaseModel):
    top_label: Optional[str] = None
    confidence: Optional[float] = None
    candidates: List[Candidate] = Field(default_factory=list)
    model_family: Optional[str] = None

class TriviaOut(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    source: Optional[str] = None

class QuestionOut(BaseModel):
    body: Optional[str] = None
    audience: Optional[str] = None

class ObservationOut(BaseModel):
    id: int
    status: str
    mediaUrl: str
    detection: Optional[DetectionOut] = None
    trivia: Optional[TriviaOut] = None
    question: Optional[QuestionOut] = None
