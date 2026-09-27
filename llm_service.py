import os
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2:3b"
)


def generate_answer(question: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": f"""
You are the answer generation module of an AI
answer verification system.

Answer the following question clearly and accurately.

Question:

{question}
""",
            "stream": False
        },
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    answer = data.get("response")

    if not answer:
        raise ValueError("LLM returned an empty response")

    return answer.strip()