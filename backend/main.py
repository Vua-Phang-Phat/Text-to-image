from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json
import requests
import base64
from langdetect import detect
from googletrans import Translator
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# Load biến môi trường từ file .env (chỉ dùng khi chạy local)
load_dotenv(dotenv_path='D:/T2I/backend/.env')

SERVICE_ACCOUNT_FILE = "D:/T2I/backend/t2image-463005-549d95606f41.json"  
DEMO_IMAGE_URL = "https://placehold.co/512x512/png?text=Demo+Image"

app = FastAPI()

# Thêm CORS cho phép mọi domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ImageRequest(BaseModel):
    prompt: str
    width: int = 1024
    height: int = 1024

def prompt_to_english(prompt: str) -> str:
    try:
        lang = detect(prompt)
        if lang != "en":
            translated = Translator().translate(prompt, dest="en").text
            print(f"[Auto-translate] '{prompt}' ({lang}) => '{translated}'")
            return translated
        return prompt
    except Exception as e:
        print("Langdetect error:", e)
        return prompt

@app.post("/generate-image")
def generate_image(req: ImageRequest):
    try:
        # Tự động dịch prompt sang tiếng Anh 
        prompt_en = prompt_to_english(req.prompt)

        # Lấy access token OAuth2 cho Vertex AI
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        creds.refresh(Request())
        access_token = creds.token

        # Endpoint Vertex AI 
        url = "https://us-central1-aiplatform.googleapis.com/v1/projects/t2image-463005/locations/us-central1/publishers/google/models/imagegeneration:predict"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "instances": [
                {
                    "prompt": prompt_en
                }
            ],
            "parameters": {
                "sampleCount": 1,
                "imageHeight": req.height,
                "imageWidth": req.width
            }
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
        if response.status_code == 200:
            result = response.json()
            # Trả về ảnh base64 nếu thành công
            try:
                image_base64 = result["predictions"][0]["bytesBase64Encoded"]
                return {"image_base64": image_base64}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Lỗi đọc kết quả: {e}\n{result}")
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    except Exception as e:
        print("ERROR:", e)
        return {
            "image_url": DEMO_IMAGE_URL,
            "mode": "demo",
            "message": f"Demo mode: {str(e)}"
        }

@app.get("/download-image/{image_id}")
def download_image(image_id: str):
    file_path = f"output/{image_id}.png"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Không tìm thấy ảnh!")
    return FileResponse(file_path, media_type="image/png", filename=f"image_{image_id}.png")
