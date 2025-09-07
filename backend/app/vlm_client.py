import os
from typing import Dict, Any

# ここで必要なプロバイダ(OpenAI/Gemini/Anthropic)を実装
# MVPではダミー応答でもOK（デモ保険）

def analyze_image(image_url: str, locale: str = "ja") -> Dict[str, Any]:
    """
    戻り値は DetectionOut/TriviaOut/QuestionOut に詰め直せるJSON
    """
    # ▼ダミー（VLM未接続でもデモ可能）
    return {
        "candidates": [
            {"ja": "キタテハ", "en": "Asian comma", "sci": "Polygonia c-aureum", "score": 0.62},
            {"ja": "テングチョウ", "en": "Nettle-tree butterfly", "sci": "Libythea celtis", "score": 0.21},
        ],
        "top_label": "キタテハ",
        "confidence": 0.62,
        "model_family": "vlm:dummy-0.1",
        "trivia": {
            "title": "羽の切れ込みの理由",
            "body": "翅のギザギザは樹皮に溶け込むカモフラージュとして働くと考えられている…（ダミー）",
            "source": None,
        },
        "question": {"body": "秋にも見られるのはなぜ？", "audience": "kid"},
        "raw": {},
    }
