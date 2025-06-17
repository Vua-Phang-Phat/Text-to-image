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
from langdetect import detect
from googletrans import Translator

# Đường dẫn file service account
SERVICE_ACCOUNT_FILE = "D:/T2I/backend/t2image-463005-549d95606f41.json"  

# Cấu hình FastAPI
app = FastAPI()

# Thêm CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model dữ liệu request
class ImageRequest(BaseModel):
    prompt: str
    width: int = 1024
    height: int = 1024

def prompt_to_english(prompt: str) -> str:
    """
    Dịch prompt sang tiếng Anh nếu là tiếng Việt hoặc bất kỳ ngôn ngữ khác, giữ nguyên nếu đã là tiếng Anh.
    """
    try:
        lang = detect(prompt)
        if lang != "en":
            try:
                translated = Translator().translate(prompt, dest="en").text
                return translated
            except Exception:
                return prompt
        else:
            return prompt
    except Exception:
        # Nếu không xác định được ngôn ngữ, giữ nguyên prompt
        return prompt

@app.post("/generate-image")
def generate_image(req: ImageRequest):
    try:
        # Dịch toàn bộ prompt sang tiếng Anh
        prompt_en = prompt_to_english(req.prompt)

        # Lấy access token OAuth2
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        creds.refresh(Request())
        access_token = creds.token

        # Endpoint Vertex AI 
        url = "https://us-central1-aiplatform.googleapis.com/v1/projects/t2image-463005/locations/us-central1/publishers/google/models/imagegeneration:predict"

        # Tạo header chuẩn
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Payload gửi lên
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

        # Gửi request đến Vertex AI
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            result = response.json()
            # Kiểm tra trường kết quả
            try:
                image_base64 = result["predictions"][0]["bytesBase64Encoded"]
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Lỗi đọc kết quả: {e}\n{result}")
            return {"image_base64": image_base64}
        else:
            # Trả về thông báo lỗi chi tiết từ Vertex AI
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download-image/{image_id}")
def download_image(image_id: str):
    file_path = f"output/{image_id}.png"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Không tìm thấy ảnh!")
    return FileResponse(file_path, media_type="image/png", filename=f"image_{image_id}.png")
