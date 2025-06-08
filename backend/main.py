from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import requests

from langdetect import detect
from googletrans import Translator

# Load biến môi trường (dùng cho local dev, không cần khi deploy Cloud Run)
load_dotenv(dotenv_path='D:/T2I/backend/.env')

STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
DEMO_IMAGE_URL = "https://placehold.co/512x512/png?text=Demo+Image"

app = FastAPI()

class ImagePrompt(BaseModel):
    prompt: str

def ensure_english(prompt: str) -> str:
    try:
        lang = detect(prompt)
    except Exception:
        lang = 'en'
    if lang != 'en':
        translator = Translator()
        translated = translator.translate(prompt, dest='en')
        print(f"[Auto-translate] Dịch từ {lang} sang en: '{prompt}' -> '{translated.text}'")
        return translated.text
    return prompt

@app.post("/generate-image")
def generate_image(prompt_in: ImagePrompt):
    """
    Nhận prompt, auto detect & dịch sang tiếng Anh nếu cần, gửi sang Stability AI, trả về ảnh.
    """
    try:
        # Auto detect và dịch prompt nếu không phải tiếng Anh
        prompt = ensure_english(prompt_in.prompt)
        api_host = "https://api.stability.ai"
        engine_id = "stable-diffusion-xl-1024-v1-0"

        url = f"{api_host}/v1/generation/{engine_id}/text-to-image"
        headers = {
            "Authorization": f"Bearer {STABILITY_API_KEY}",
            "Accept": "application/json"
        }
        payload = {
            "text_prompts": [{"text": prompt}],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            res = response.json()
            # Stability AI trả về ảnh base64
            if "artifacts" in res and len(res["artifacts"]) > 0:
                base64_image = res["artifacts"][0]["base64"]
                return {"image_base64": base64_image, "mode": "stability"}
        else:
            print("Stability API ERROR:", response.status_code, response.text)
            raise Exception(f"Stability AI API error: {response.status_code}, {response.text}")

    except Exception as e:
        print("ERROR:", e)
        return {
            "image_url": DEMO_IMAGE_URL,
            "mode": "demo",
            "message": f"Demo mode: {str(e)}"
        }
