import os
from vectorstore_store import load_vector, save_vector
import io
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from uuid import uuid4
from models import ChatRequest, ChatResponse, SessionResponse, Message
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from chatbot import create_chat_model, format_history, create_stream_chat_model
from history import load_history, save_history
from typing import AsyncGenerator
from fastapi.exceptions import HTTPException
import PyPDF2
# For Pdf
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA


app = FastAPI()

chat_model = create_chat_model()
stream_chat_model = create_stream_chat_model()
app.add_middleware(CORSMiddleware,
                   allow_origins=["*"],
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"]
                   )
embeddings = OpenAIEmbeddings()


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


@app.post('/upload-pdf')
async def upload_pdf(session_id: str = Form(...), file: UploadFile = File(...)):
    if file.content_type != 'application/pdf':
        raise HTTPException(
            status_code=400, detail="Please upload Pdf file only!")
    contents = await file.read()
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text+"\n"
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)

    vectorstore = FAISS.from_texts(chunks, embeddings)
    save_vector(session_id, vectorstore)
    return JSONResponse(status_code=200, content={'res': "PDF uploaded and processed successfully."})


@app.post('/chat-pdf')
async def chat_pdf(request: ChatRequest):
    pdf_vectors = [name.split('.')[0]
                   for name in os.listdir('./db/vectorstore')]
    if request.session_id not in pdf_vectors:
        raise HTTPException(
            status_code=400, detail="No PDF uploaded for this session.")
    vectorstore = load_vector(
        session_id=request.session_id, embeddings=embeddings)
    answer = "Answer not Found!"
    if vectorstore:
        qa_chain = RetrievalQA.from_chain_type(
            llm=chat_model,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(
                search_kwargs={"k": 3})
        )
        answer = qa_chain.run(request.message)
    return JSONResponse(status_code=200, content={"res": answer})
