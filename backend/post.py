import httpx
import os
from dotenv import load_dotenv
import base64
import google.generativeai as genai

# .env の内容を環境変数に読み込む
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")
image_path = "https://www.kankomie.or.jp/rails/active_storage/representations/proxy/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaHBBM09QQkE9PSIsImV4cCI6bnVsbCwicHVyIjoiYmxvYl9pZCJ9fQ==--33f932ed38f410d3a8887af60c87605b798d81c0/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaDdCem9MWm05eWJXRjBPZ2wzWldKd09oSnlaWE5wZW1WZmRHOWZabWwwV3dkcEFvQUhNQT09IiwiZXhwIjpudWxsLCJwdXIiOiJ2YXJpYXRpb24ifX0=--dfa0c65638d6abc421e5d17fd19f8fe5621853cd/0D9A3979-1600x1067.jpg"

image = httpx.get(image_path)

prompt = """この画像に写っている物体を分析して、以下のマークダウンフォーマットで回答してください：

## 検知した物体の名前
[物体の名前]

## はっけん
[物体の詳細な説明、特徴、生態、用途などを含む]

## 問い
[その物体に関する興味深い質問を1つ]"""

print("start")
response = model.generate_content(
    [{'mime_type': 'image/jpeg', 'data': base64.b64encode(image.content).decode('utf-8')}, prompt])

print("end", response.text)
