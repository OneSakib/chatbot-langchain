from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
import os
load_dotenv()


def create_chat_model():
    return ChatOpenAI(model=)
