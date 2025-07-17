from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
import os
load_dotenv()


def create_chat_model():
    return ChatOpenAI(model="gpt-3.5-turbo",  temperature=0,)


def create_stream_chat_model():
    return ChatOpenAI(model="gpt-3.5-turbo", streaming=True, temperature=0,)


def format_history(history):
    formatted = []
    for msg in history:
        if msg['role'] == 'user':
            formatted.append(HumanMessage(content=msg['content']))
        else:
            formatted.append(AIMessage(content=msg['content']))

    return formatted
