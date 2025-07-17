from pydantic import BaseModel
from typing import List


class Message(BaseModel):
    rols: str
    content: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    response: str
    history: List[Message]


class SessionResponse(BaseModel):
    session_id: str
