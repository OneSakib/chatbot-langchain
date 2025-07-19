from langchain_community.vectorstores import FAISS
import os
import json
from typing import List, Dict
from models import Message
import pickle
DATA_DIR = "db/vectorstore"
os.makedirs(DATA_DIR, exist_ok=True)


def _get_file_path(session_id: str) -> str:
    return os.path.join(DATA_DIR, f"{session_id}.text")


def load_vector(session_id: str, embeddings):
    file_path = _get_file_path(session_id)
    if not os.path.exists(file_path):
        return None
    return FAISS.load_local(file_path, embeddings, allow_dangerous_deserialization=True)


def save_vector(session_id: str, vectorstore):
    file_path = _get_file_path(session_id)
    vectorstore.save_local(file_path)
