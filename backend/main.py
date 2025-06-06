from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate-image")
def generate_image(request: PromptRequest):
    # Ví dụ với Gemini API, bạn chỉnh lại endpoint thực tế theo tài liệu Google
    endpoint = "https://YOUR_VERTEX_AI_ENDPOINT/v1beta/generateImage"
    headers = {
        "Authorization": f"Bearer {os.getenv('GEMINI_API_KEY')}",
        "Content-Type": "application/json"
    }
    body = {
        "prompt": request.prompt
    }
    resp = requests.post(endpoint, headers=headers, json=body)
    if resp.status_code == 200:
        data = resp.json()
        return {"image_url": data["imageUrl"]}  # Tuỳ response thực tế
    else:
        raise HTTPException(status_code=500, detail="AI API Error")
