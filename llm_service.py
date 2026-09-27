import requests


def generate_answer(question: str) -> str:

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2:3b",
            "prompt": f"""
You are the answer generation module of an AI
answer verification system.

Answer the following question clearly and accurately.

Question:
{question}
""",
            "stream": False
        }
    )

    response.raise_for_status()

    data = response.json()

    return data["response"]