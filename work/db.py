from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["scene_frame_split_db"]

scenes_col = db["scenes"]
frames_col = db["frames"]