import os
from scene_split import detect_scenes  # Doit inclure la nouvelle logique d’extraction de frames
from utils import save_file_async

UPLOAD_FOLDER = "uploads"

async def upload_video(file):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    saved_path = await save_file_async(file, UPLOAD_FOLDER)
    return {"uploaded_path": saved_path}

def detect_video_scenes(video_path, threshold=0.5):
    if not os.path.isfile(video_path):
        return {"error": f"Le fichier vidéo '{video_path}' n'existe pas."}

    scenes = detect_scenes(video_path, threshold)  # Appelle la version enrichie
    return {
        "video": os.path.basename(video_path),
        "total_scenes": len(scenes),
        "scenes": scenes
    }

def export_scenes(video_path, format="json"):
    if not os.path.isfile(video_path):
        return {"error": f"Le fichier vidéo '{video_path}' n'existe pas."}

    scenes = detect_scenes(video_path)  # Déclenche aussi l'extraction des frames
    if format.lower() == "csv":
        lines = ["scene_id,start,end"]
        lines += [f"{s['scene_id']},{s['start']},{s['end']}" for s in scenes]
        return {"format": "csv", "content": "\n".join(lines)}

    return {"format": "json", "content": scenes}
