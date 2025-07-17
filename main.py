from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from uuid import uuid4
from models import ChatRequest, ChatResponse, SessionResponse, Message
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from chatbot import create_chat_model, format_history, create_stream_chat_model
from history import load_history, save_history
from typing import AsyncGenerator


app = FastAPI()

chat_model = create_chat_model()
stream_chat_model = create_stream_chat_model()
app.add_middleware(CORSMiddleware,
                   allow_origins=["*"],
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"]
                   )


@app.get('/login', response_model=SessionResponse)
def login():
    session_id = str(uuid4())
    return {'session_id': session_id}


@app.post('/chat', response_model=ChatResponse)
def chat(request: ChatRequest):
    history = load_history(session_id=request.session_id)
    formatted_history = format_history(history)
    user_msg = {"role": "user", "content": request.message}
    formatted_history.append(HumanMessage(content=request.message))
    response = chat_model.invoke(formatted_history)
    bot_msg = {"role": "assistant", "content": response.content}
    history.extend([user_msg, bot_msg])
    save_history(session_id=request.session_id, history=history)
    return ChatResponse(session_id=request.session_id, response=str(response.content), history=[Message(**msg) for msg in history])


@app.post('/chat-stream')
def chat_stream(request: ChatRequest):
    history = load_history(session_id=request.session_id)
    formatted_history = format_history(history)
    user_msg = {"role": "user", "content": request.message}
    formatted_history.append(HumanMessage(content=request.message))

    async def response_generator() -> AsyncGenerator[str, None]:
        yield ""
        response_text = ""
        async for chunk in stream_chat_model.astream(formatted_history):
            if chunk.content:
                response_text += str(chunk.content)
                yield str(chunk.content)
        # Save History
        bot_msg = {"role": "assistant", "content": response_text}
        history.extend([user_msg, bot_msg])
        save_history(session_id=request.session_id, history=history)
    return StreamingResponse(response_generator(), media_type="text/plain")
