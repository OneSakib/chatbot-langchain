import streamlit as st
import requests
import uuid

# Adjust if your FastAPI server is hosted elsewhere
API_BASE = "http://localhost:8000"

st.set_page_config(page_title="LangChain Chatbot", page_icon="🤖")
st.title("🤖 GPT-4 Chatbot with PDF Q&A")

# Initialize session state for session ID and chat history
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "history" not in st.session_state:
    st.session_state.history = []

# Login / get session ID


def login():
    res = requests.get(f"{API_BASE}/login")
    session_id = res.json()["session_id"]
    st.session_state.session_id = session_id
    st.success(f"Session started: {session_id}")


if not st.session_state.session_id:
    if st.button("Start New Chat"):
        login()
    st.stop()

st.sidebar.header("PDF Upload")
uploaded_pdf = st.sidebar.file_uploader(
    "Upload a PDF (confidential)", type=["pdf"])

if uploaded_pdf:
    # Upload PDF to backend
    files = {"file": (uploaded_pdf.name, uploaded_pdf, "application/pdf")}
    data = {"session_id": st.session_state.session_id}
    with st.spinner("Uploading and processing PDF..."):
        res = requests.post(f"{API_BASE}/upload-pdf", data=data, files=files)
        if "error" in res.json():
            st.error(res.json()["error"])
        else:
            st.success("PDF uploaded and processed!")

st.header("Chat")

# Display existing chat history
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input area
mode = st.radio("Choose mode", options=["General Chat", "Ask PDF"], index=0)

if prompt := st.chat_input("Type your message..."):
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if mode == "General Chat":
        with st.chat_message("assistant"):
            response_container = st.empty()
            url = f"{API_BASE}/chat-stream"
            headers = {"Content-Type": "application/json"}
            data = {
                "session_id": st.session_state.session_id,
                "message": prompt
            }
            response = requests.post(url, json=data, stream=True)
            full_reply = ""
            for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
                if chunk:
                    full_reply += chunk
                    response_container.markdown(full_reply + "▌")
            response_container.markdown(full_reply)
            st.session_state.history.append(
                {"role": "assistant", "content": full_reply})
    else:  # Ask PDF mode
        with st.chat_message("assistant"):
            res = requests.post(
                f"{API_BASE}/chat-pdf",
                json={"session_id": st.session_state.session_id, "message": prompt}
            )
            json_res = res.json()
            if "error" in json_res:
                answer = json_res["error"]
            else:
                answer = json_res["response"]
            st.markdown(answer)
            st.session_state.history.append(
                {"role": "assistant", "content": answer})
