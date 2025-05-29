from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from scene_split_logic import process_video, get_scenes_by_video_name, get_frames_by_video_name,delete_video_data
import os
from db import scenes_col, frames_col
from fastapi import Query
from fastapi.responses import JSONResponse

app = FastAPI(title="Video Scene Splitter Service")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crée le dossier de frames statiques si inexistant
os.makedirs("static/frames", exist_ok=True)

# Permettre l'accès aux frames via URL
app.mount("/static", StaticFiles(directory="static"), name="static")

# 📤 Route d’upload + détection de scènes
@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    return await process_video(file)

# 📄 Récupérer les scènes d’une vidéo donnée
@app.get("/scenes/{video_name}")
async def get_scenes(video_name: str):
    return get_scenes_by_video_name(video_name)

# 🖼️ Récupérer les frames extraites pour une vidéo donnée
@app.get("/frames/{video_name}")
async def get_frames(video_name: str):
    return get_frames_by_video_name(video_name)


@app.delete("/delete")
def delete(filename: str = Query(...)):
    try:
        deleted = delete_video_data(filename)
        if deleted:
            return {"message": f"✅ Vidéo '{filename}' et données supprimées"}
        raise HTTPException(status_code=404, detail="Fichier non trouvé ou aucune donnée supprimée.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Récupérer les scènes
@app.get("/scenes/{video_name}")
async def get_scenes(video_name: str):
    return get_scenes_by_video_name(video_name)

# Récupérer les frames
@app.get("/frames/{video_name}")
async def get_frames(video_name: str):
    return get_frames_by_video_name(video_name)
