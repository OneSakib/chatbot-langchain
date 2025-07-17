import streamlit as st
import requests
import uuid

API_BASE = "http://localhost:8000" 

st.set_page_config(page_title="LangChain Chatbot", page_icon="🤖")

st.title("🤖 GPT-4 Chatbot (Streamed)")

# Session ID initialization
if "session_id" not in st.session_state:
    st.session_state.session_id = None

# Chat history init
if "history" not in st.session_state:
    st.session_state.history = []

# Login / get session


def login():
    res = requests.get(f"{API_BASE}/login")
    session_id = res.json()["session_id"]
    st.session_state.session_id = session_id
    st.success(f"🔐 Session started: {session_id}")


if not st.session_state.session_id:
    if st.button("Start New Chat"):
        login()
    st.stop()

# Display message history
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle user input
if prompt := st.chat_input("Type your message..."):
    # Append user message immediately
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_container = st.empty()

        # Stream from FastAPI `/chat-stream`
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
                response_container.markdown(full_reply + "▌")  # typing effect

        response_container.markdown(full_reply)  # Final update
        st.session_state.history.append(
            {"role": "assistant", "content": full_reply})
