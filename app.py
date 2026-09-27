from fastapi import FastAPI
from pydantic import BaseModel

from llm_service import generate_answer
from database import get_connection


app = FastAPI(
    title="Multi-Agent AI Answer Verification System",
    description="Backend for answer generation and verification",
    version="0.1.0"
)


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def home():
    return {
        "message": "AI Answer Verification Backend is running"
    }


@app.post("/generate-answer")
def generate(request: QuestionRequest):

    # 1. Generate answer using LLM
    answer = generate_answer(request.question)

    # 2. Connect to PostgreSQL
    connection = get_connection()
    cursor = connection.cursor()

    # 3. Save question and answer
    cursor.execute(
        """
        INSERT INTO questions_answers (question, answer)
        VALUES (%s, %s)
        """,
        (request.question, answer)
    )

    # 4. Save the transaction
    connection.commit()

    # 5. Close database resources
    cursor.close()
    connection.close()

    # 6. Return the result
    return {
        "question": request.question,
        "answer": answer
    }