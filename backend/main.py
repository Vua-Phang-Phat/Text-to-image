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
from google.auth.transport.requests import Request as GoogleAuthRequest
from fastapi import Request as FastAPIRequest
from google.auth import default

from google.cloud import storage
from google.cloud import firestore
from datetime import datetime
from fastapi import Query
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import FastAPI, HTTPException, Depends

if not firebase_admin._apps:
    firebase_admin.initialize_app()

# định nghĩa model lịch sử
db = firestore.Client(database="sql1999")
HISTORY_COLLECTION = "search_history"

BUCKET_NAME = "t2image-bucket"  # Tên bucket bạn đã tạo trên Cloud Storage
def upload_to_bucket(file_bytes, filename, bucket_name=BUCKET_NAME):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_string(file_bytes, content_type="image/png")
    return f"https://storage.googleapis.com/{bucket_name}/{filename}"

# Load .env khi local
load_dotenv(dotenv_path='D:/T2I/backend/.env')

DEMO_IMAGE_URL = "https://placehold.co/512x512/png?text=Demo+Image"

app = FastAPI()

# ====== HÀM ĐỒNG BỘ USER VÀO FIRESTORE (CHỈ THÊM MỚI, KHÔNG SỬA CODE CŨ) ======
def sync_user_to_firestore(user_info):
    print("SYNC USER TO FIRESTORE:", user_info)
    users_ref = db.collection("users")
    doc_ref = users_ref.document(user_info["uid"])
    now = datetime.utcnow()
    doc = doc_ref.get()

    if not doc.exists:
        doc_ref.set({
            "uid": user_info["uid"],
            "email": user_info.get("email"),
            "role": "user",      # mặc định là user
            "status": "active",  # mặc định là active
            "created_at": now,
            "last_login": now
        })
    else:
        doc_ref.update({"last_login": now})
# Hàm xác thực token gửi lên từ client
def verify_token(request: FastAPIRequest):
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    try:
        id_token = auth_header.split(" ")[1]
    except Exception:
        raise HTTPException(status_code=401, detail="Malformed Authorization header")
    try:
        decoded_token = auth.verify_id_token(id_token)
        # ======= THÊM ĐOẠN ĐỒNG BỘ USER VÀO FIRESTORE NGAY SAU KHI XÁC THỰC =======
        user_info = {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email"),
        }
        sync_user_to_firestore(user_info)

        return decoded_token
    except Exception as e:
        print(f"Error verifying token: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {e}")

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
        print("DEBUG -- Request class:", type(GoogleAuthRequest()))
        print("DEBUG -- Request module:", type(GoogleAuthRequest()).__module__)

        creds.refresh(GoogleAuthRequest())
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
            # KIỂM TRA kỹ trường predictions
            if (
                isinstance(result, dict)
                and "predictions" in result
                and isinstance(result["predictions"], list)
                and len(result["predictions"]) > 0
                and "bytesBase64Encoded" in result["predictions"][0]
                and result["predictions"][0]["bytesBase64Encoded"]
            ):
                try:
                    image_base64 = result["predictions"][0]["bytesBase64Encoded"]
                    filename = f"{uuid.uuid4().hex}.png"
                    file_bytes = base64.b64decode(image_base64)
                    download_url = upload_to_bucket(file_bytes, filename)
                    save_search_history(req.prompt, download_url)
                    return {
                        "image_base64": image_base64,
                        "download_url": download_url,
                        "share_url": download_url,
                        "image_url": download_url,
                    }
                except Exception as e:
                    print("ERROR decode image:", e, result)
                    raise HTTPException(status_code=500, detail=f"Lỗi đọc kết quả: {e}\n{result}")
            else:
                # Log lại kết quả trả về khi không đúng cấu trúc
                print("API result thiếu predictions hoặc bị chặn prompt:", result)
                raise HTTPException(
                    status_code=400,
                    detail=f"Không thể sinh ảnh với prompt này (có thể prompt bị chặn hoặc response không hợp lệ). Thông tin: {result}"
                )
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

@app.delete("/search-history/{history_id}")
def delete_search_history(history_id: str):
    doc_ref = db.collection(HISTORY_COLLECTION).document(history_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Lịch sử không tồn tại")
    doc_ref.delete()
    return {"message": "Xóa lịch sử thành công"}

# Route mẫu bảo vệ bởi xác thực
@app.get("/me")
def get_me(user=Depends(verify_token)):
    return {
        "uid": user["uid"],
        "email": user.get("email"),
        "name": user.get("name")
    }

# API: Lấy danh sách user (chỉ cho admin)
@app.get("/users")
def list_users(user=Depends(verify_token)):
    users_ref = db.collection("users")
    current_uid = user["uid"]
    me = users_ref.document(current_uid).get()
    if not me.exists or me.to_dict().get("role") != "admin":
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập")
    docs = users_ref.limit(100).stream()
    return [{**doc.to_dict(), "id": doc.id} for doc in docs]


# API: Đổi quyền user (chỉ cho admin)
class UpdateRoleRequest(BaseModel):
    role: str

@app.post("/users/{uid}/role")
def update_user_role(uid: str, data: UpdateRoleRequest, user=Depends(verify_token)):
    users_ref = db.collection("users")
    current_uid = user["uid"]
    me = users_ref.document(current_uid).get()
    if not me.exists or me.to_dict().get("role") != "admin":
        raise HTTPException(status_code=403, detail="Bạn không có quyền phân quyền")
    doc_ref = users_ref.document(uid)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Không tìm thấy user")
    doc_ref.update({"role": data.role})
    return {"message": f"Đã đổi role user {uid} thành {data.role}"}

# Model cho cập nhật status
class UpdateStatusRequest(BaseModel):
    status: str  # "active" hoặc "blocked"

@app.post("/users/{uid}/status")
def update_user_status(uid: str, data: UpdateStatusRequest, user=Depends(verify_token)):
    users_ref = db.collection("users")
    # Kiểm tra current user có phải admin không
    current_uid = user["uid"]
    me = users_ref.document(current_uid).get()
    if not me.exists or me.to_dict().get("role") != "admin":
        raise HTTPException(status_code=403, detail="Bạn không có quyền phân quyền")
    # tương tự check admin, rồi:
    doc_ref = users_ref.document(uid)
    doc = doc_ref.get()
    if not doc.exists:
         raise HTTPException(status_code=404, detail="Không tìm thấy user")
    # cập nhật status
    doc_ref.update({"status": data.status})
    return {"message": f"Đã đổi status thành {data.status}"}

