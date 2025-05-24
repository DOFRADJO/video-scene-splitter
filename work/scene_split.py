import cv2
import datetime
import os
from db import scenes_col, frames_col  # Assure-toi que ce fichier contient bien la connexion MongoDB

def format_time(seconds):
    """Convertit un nombre de secondes en hh:mm:ss"""
    return str(datetime.timedelta(seconds=int(seconds)))

def detect_scenes(video_path, threshold=0.5):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Erreur lors de l'ouverture de la vidéo : {video_path}")
        return []

    scenes = []
    prev_hist = None
    start_time = 0.0
    scene_id = 1
    fps = cap.get(cv2.CAP_PROP_FPS)
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
                end_time = time
                scene = {
                    "scene_id": scene_id,
                    "start": format_time(start_time),
                    "end": format_time(end_time),
                    "video_name": video_name
                }
                scenes.append(scene)
                scenes_col.update_one(
                    {"video_name": video_name, "scene_id": scene_id},
                    {"$set": scene},
                    upsert=True
                )
                extract_scene_frames(video_path, start_time, end_time, scene_id, video_name, fps)
                scene_id += 1
                start_time = time

        prev_hist = hist

    # Ajouter la dernière scène
    final_scene = {
        "scene_id": scene_id,
        "start": format_time(start_time),
        "end": format_time(last_time),
        "video_name": video_name
    }
    scenes.append(final_scene)
    scenes_col.update_one(
        {"video_name": video_name, "scene_id": scene_id},
        {"$set": final_scene},
        upsert=True
    )
    extract_scene_frames(video_path, start_time, last_time, scene_id, video_name, fps)

    cap.release()
    return scenes

def extract_scene_frames(video_path, start_time, end_time, scene_id, video_name, fps):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return

    start_sec = int(start_time)
    end_sec = int(end_time)

    # Toujours extraire au moins une frame, même si la durée est < 1 seconde
    if start_sec == end_sec:
        timestamps = [end_sec]
    else:
        timestamps = list(range(start_sec, end_sec))

    for sec in timestamps:
        cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
        ret, frame = cap.read()
        if not ret:
            continue

        frame_id = f"{scene_id}_{sec}"
        frame_data = {
            "scene_id": scene_id,
            "video_name": video_name,
            "frame_id": frame_id,
            "timestamp": sec
        }
        frames_col.update_one(
            {"scene_id": scene_id, "timestamp": sec},
            {"$set": frame_data},
            upsert=True
        )

    cap.release()
