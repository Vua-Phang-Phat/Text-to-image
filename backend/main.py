from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.auth import default
from google.auth.transport.requests import Request
import requests
import json
import os
from langdetect import detect
from googletrans import Translator

# Cấu hình FastAPI
app = FastAPI()

# Cho phép tất cả origin gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model dữ liệu cho request
class ImageRequest(BaseModel):
    prompt: str
    width: int = 1024
    height: int = 1024

# Hàm dịch prompt sang tiếng Anh nếu cần
def prompt_to_english(prompt: str) -> str:
    try:
        lang = detect(prompt)
        if lang != "en":
            return Translator().translate(prompt, dest="en").text
        return prompt
    except Exception:
        return prompt

@app.post("/generate-image")
def generate_image(req: ImageRequest):
    try:
        # Dịch prompt sang tiếng Anh nếu cần
        prompt_en = prompt_to_english(req.prompt)

        # Lấy access token từ Application Default Credentials (Cloud Run)
        creds, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        creds.refresh(Request())
        access_token = creds.token

        # Đọc thông tin cấu hình từ biến môi trường
        project_id = os.environ.get("PROJECT_ID")
        location = os.environ.get("LOCATION", "us-central1")
        model_id = os.environ.get("MODEL_ID", "imagegeneration")

        # Gọi đến Vertex AI
        url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model_id}:predict"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "instances": [{"prompt": prompt_en}],
            "parameters": {
                "sampleCount": 1,
                "imageHeight": req.height,
                "imageWidth": req.width
            }
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            result = response.json()
            try:
                image_base64 = result["predictions"][0]["bytesBase64Encoded"]
                return {"image_base64": image_base64}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Lỗi đọc kết quả: {e}\n{result}")
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
