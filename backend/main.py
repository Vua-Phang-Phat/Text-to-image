from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import requests
import json
import os
import base64
from uuid import uuid4
from dotenv import load_dotenv
from langdetect import detect
from googletrans import Translator

# Load biến môi trường từ file .env
load_dotenv()

# Lấy thông tin cấu hình từ biến môi trường
service_account_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "./t2image-463005-549d95606f41.json")
project_id = os.environ.get("PROJECT_ID")
location = os.environ.get("GCP_REGION", "us-central1")
model_name = os.environ.get("MODEL_NAME", "publishers/google/models/imagegeneration")

# Load credentials từ file Service Account JSON 
creds = service_account.Credentials.from_service_account_file(
    service_account_path,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)
creds.refresh(Request())
print("🔐 Project ID từ file JSON:", creds.project_id)  # In ra project đang dùng thật sự

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

# Hàm dịch prompt sang tiếng Anh
def prompt_to_english(prompt: str) -> str:
    try:
        lang = detect(prompt)
        if lang != "en":
            return Translator().translate(prompt, dest="en").text
        return prompt
    except Exception:
        return prompt

# API sinh ảnh từ prompt
@app.post("/generate-image")
def generate_image(req: ImageRequest):
    try:
        prompt_en = prompt_to_english(req.prompt)
        access_token = creds.token

        url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/{model_name}:predict"
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

                # Lưu file ảnh ra thư mục 'generated'
                image_data = base64.b64decode(image_base64)
                file_name = f"{uuid4().hex}.png"
                os.makedirs("generated", exist_ok=True)
                file_path = os.path.join("generated", file_name)
                with open(file_path, "wb") as f:
                    f.write(image_data)

                return {
                    "image_base64": image_base64,
                    "download_url": f"/download-image/{file_name}",
                    "share_url": f"/share-image/{file_name}"
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Lỗi đọc kết quả: {e}\n{result}")
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API tải ảnh 
@app.get("/download-image/{filename}")
def download_image(filename: str):
    file_path = os.path.join("generated", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="image/png", filename=filename)

# API chia sẻ ảnh 
@app.get("/share-image/{filename}")
def share_image(filename: str):
    # Ở bản thật có thể trả về link public (Firebase, Cloud Storage)
    return {
        "message": "Đây là link chia sẻ tạm thời",
        "share_link": f"http://127.0.0.1:8000/download-image/{filename}"
    }
