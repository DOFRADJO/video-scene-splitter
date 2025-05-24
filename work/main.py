from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from scene_service import (
    upload_video,
    detect_video_scenes,
    export_scenes
)

app = FastAPI(title="Video Scene Detection Microservice")

# 🔄 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod, restreindre à ["http://localhost:3000"] ou autre
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📁 Création dossier upload
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 🌐 Accès statique aux vidéos uploadées
app.mount("/videos", StaticFiles(directory=UPLOAD_DIR), name="videos")

@app.get("/")
def home():
    return {"message": "Bienvenue sur le microservice de détection de scènes vidéo"}

# 📤 Upload vidéo
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    return await upload_video(file)

# 🎞️ Split automatique des scènes + frames
@app.post("/split_scene")
def split_scene(video_filename: str = Form(...), threshold: float = Form(0.5)):
    video_path = os.path.join(UPLOAD_DIR, video_filename)
    result = detect_video_scenes(video_path, threshold)
    if "error" in result:
        return result
    return {
        "message": f"{len(result['scenes'])} scènes détectées et enregistrées.",
        "scenes": result["scenes"]
    }

# 🧾 Export JSON ou CSV
@app.get("/export")
def export(video_filename: str, format: str = "json"):
    video_path = os.path.join(UPLOAD_DIR, video_filename)
    return export_scenes(video_path, format)
