import os
import json
from typing import List, Dict
from models import Message

DATA_DIR = "db/history"

os.makedirs(DATA_DIR, exist_ok=True)


def _get_file_path(session_id: str) -> str:
    return os.path.join(DATA_DIR, f"{session_id}.json")


def load_history(session_id: str) -> List[Dict]:
    file_path = _get_file_path(session_id)
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r') as f:
        return json.load(f)


def save_history(session_id: str, history: List[Dict]):
    file_path = _get_file_path(session_id)
    with open(file_path, 'w') as f:
        json.dump(history, f, indent=4)
