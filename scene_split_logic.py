import os
import cv2
import datetime
from fastapi import UploadFile
from db import scenes_col, frames_col


async def save_file_async(file: UploadFile, folder: str):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, os.path.basename(file.filename))
    with open(path, "wb") as f:
        content = await file.read()
        f.write(content)
    return path


def format_time(seconds):
    return str(datetime.timedelta(seconds=int(seconds)))


def extract_scene_frames(video_path, start_time, end_time, scene_id, video_name, fps):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return

    start_sec = int(start_time)
    end_sec = max(int(end_time), start_sec + 1)

    output_folder = os.path.join("static/frames", video_name)
    os.makedirs(output_folder, exist_ok=True)

    for sec in range(start_sec, end_sec):
        cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
        ret, frame = cap.read()
        if not ret:
            continue

        frame_id = f"scene{scene_id}_{sec}"
        image_path = os.path.join(output_folder, f"{frame_id}.jpg")
        cv2.imwrite(image_path, frame)

        frame_data = {
            "scene_id": scene_id,
            "video_name": video_name,
            "frame_id": frame_id,
            "timestamp": sec,
            "image_path": image_path
        }

        frames_col.update_one(
            {"scene_id": scene_id, "timestamp": sec},
            {"$set": frame_data},
            upsert=True
        )

    cap.release()


def detect_scenes(video_path, threshold=0.5):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []

    scenes = []
    prev_hist, start_time = None, 0.0
    scene_id, fps = 1, cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    last_time = 0.0
    video_name = os.path.basename(video_path)

    for i in range(frame_count):
        ret, frame = cap.read()
        if not ret:
            break

        time = i / fps
        last_time = time

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = cv2.normalize(hist, hist).flatten()

        if prev_hist is not None:
            diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA)
            if diff > threshold:
                scenes.append(store_scene(start_time, time, scene_id, video_name, video_path, fps))
                scene_id += 1
                start_time = time
        prev_hist = hist

    scenes.append(store_scene(start_time, last_time, scene_id, video_name, video_path, fps))
    cap.release()
    return scenes


def store_scene(start_time, end_time, scene_id, video_name, video_path, fps):
    scene = {
        "scene_id": scene_id,
        "start": format_time(start_time),
        "end": format_time(end_time),
        "video_name": video_name
    }
    scenes_col.update_one(
        {"video_name": video_name, "scene_id": scene_id},
        {"$set": scene},
        upsert=True
    )
    extract_scene_frames(video_path, start_time, end_time, scene_id, video_name, fps)
    return scene


async def process_video(file: UploadFile):
    path = await save_file_async(file, "videos")
    video_name = os.path.basename(path)
    scenes = detect_scenes(path)

    # 🔁 Récupération des frames groupées par scene_id
    grouped_frames = {}
    for frame in frames_col.find({"video_name": video_name}, {"_id": 0}):
        sid = frame["scene_id"]
        grouped_frames.setdefault(sid, []).append(frame)

    # 🧩 Assemblage des scènes avec leurs frames
    for scene in scenes:
        sid = scene["scene_id"]
        scene["frames"] = grouped_frames.get(sid, [])

    return {"video": video_name, "scenes": scenes}


# 🔎 Fonction utilitaire pour accès externe
def get_scenes_by_video_name(video_name: str):
    return list(scenes_col.find({"video_name": video_name}, {"_id": 0}))


def get_frames_by_video_name(video_name: str):
    return list(frames_col.find({"video_name": video_name}, {"_id": 0}))


def delete_video_data(video_name: str):
    # Supprime les scènes
    scenes_col.delete_many({"video_name": video_name})
    # Supprime les frames
    frames_col.delete_many({"video_name": video_name})
    # Supprime le fichier vidéo
    video_path = os.path.join("videos", video_name)
    if os.path.exists(video_path):
        os.remove(video_path)
    # Supprime les images de frames
    frame_dir = os.path.join("static/frames", video_name)
    if os.path.isdir(frame_dir):
        for filename in os.listdir(frame_dir):
            os.remove(os.path.join(frame_dir, filename))
        os.rmdir(frame_dir)
