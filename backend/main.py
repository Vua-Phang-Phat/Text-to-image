from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import requests

# Load biến môi trường từ file .env
load_dotenv(dotenv_path='D:/T2I/backend/.env')

STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
DEMO_IMAGE_URL = "https://placehold.co/512x512/png?text=Demo+Image"

app = FastAPI()

class ImagePrompt(BaseModel):
    prompt: str

@app.post("/generate-image")
def generate_image(prompt_in: ImagePrompt):
    """
    Sinh ảnh bằng Stability AI API. Nếu lỗi trả về ảnh demo.
    """
    try:
        api_host = "https://api.stability.ai"
        engine_id = "stable-diffusion-xl-1024-v1-0"  # Model tốt nhất, có thể đổi sang 'stable-diffusion-v1-5' nếu muốn

        url = f"{api_host}/v1/generation/{engine_id}/text-to-image"

        headers = {
            "Authorization": f"Bearer {STABILITY_API_KEY}",
            "Accept": "application/json"
        }
        payload = {
            "text_prompts": [
                {
                    "text": prompt_in.prompt
                }
            ],
            "cfg_scale": 7,  # độ chi tiết ảnh
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
                # Bạn có thể trả về base64 hoặc convert sang URL tạm (tuỳ UI/frontend)
                return {
                    "image_base64": base64_image,
                    "mode": "stability"
                }
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
