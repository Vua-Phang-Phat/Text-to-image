from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json
import requests
import base64
import uuid
from langdetect import detect
from googletrans import Translator
from google.auth.transport.requests import Request
from google.auth import default

from google.cloud import firestore
from datetime import datetime
from fastapi import Query
# định nghĩa model lịch sử
db = firestore.Client(database="sql1999")
HISTORY_COLLECTION = "search_history"



# Load .env khi local
load_dotenv(dotenv_path='D:/T2I/backend/.env')

DEMO_IMAGE_URL = "https://placehold.co/512x512/png?text=Demo+Image"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)
app.mount("/images", StaticFiles(directory=IMAGE_DIR), name="images")

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
        prompt_en = prompt_to_english(req.prompt)

        # Lấy credentials mặc định Cloud Run
        creds, project = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        creds.refresh(Request())
        access_token = creds.token

        url = "https://us-central1-aiplatform.googleapis.com/v1/projects/t2image-463005/locations/us-central1/publishers/google/models/imagegeneration:predict"
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

        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
        if response.status_code == 200:
            result = response.json()
            try:
                image_base64 = result["predictions"][0]["bytesBase64Encoded"]
                filename = f"{uuid.uuid4().hex}.png"
                file_path = os.path.join(IMAGE_DIR, filename)
                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(image_base64))
                domain = os.environ.get('DOMAIN', 't2image-875771204141.us-central1.run.app')
                download_url = f"https://{domain}/images/{filename}"
                save_search_history(req.prompt, download_url)
                return {
                    "image_base64": image_base64,
                    "download_url": download_url,
                    "share_url": download_url,
                    "image_url": download_url,
                }
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
def save_search_history(prompt, image_url, user_id=None):
    doc = {
        "prompt": prompt,
        "image_url": image_url,
        "created_at": datetime.utcnow(),
    }
    if user_id:
        doc["user_id"] = user_id
    db.collection(HISTORY_COLLECTION).add(doc)


@app.get("/download/{filename}")
def download_image(filename: str):
    file_path = os.path.join(IMAGE_DIR, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Không tìm thấy file")
    return FileResponse(file_path, filename=filename, media_type="image/png")

@app.get("/search-history")
def get_search_history(limit: int = Query(20), user_id: str = None):
    q = db.collection(HISTORY_COLLECTION).order_by("created_at", direction=firestore.Query.DESCENDING)
    if user_id:
        q = q.where("user_id", "==", user_id)
    docs = q.limit(limit).stream()
    return [
        {**doc.to_dict(), "id": doc.id}
        for doc in docs
    ]

