from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from llm_service import generate_answer
from database import get_connection


app = FastAPI(
    title="Multi-Agent AI Answer Verification System",
    description="Backend for answer generation and verification",
    version="0.2.0"
)


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question to answer")


class AnswerResponse(BaseModel):
    question_id: int
    question: str
    answer: str
    status: str


@app.get("/")
def home():
    return {
        "message": "AI Answer Verification Backend is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/generate-answer", response_model=AnswerResponse)
def generate(request: QuestionRequest):

    # 1. Generate answer using LLM
    try:
        answer = generate_answer(request.question)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="LLM service is unavailable"
        )

    # 2. Connect to PostgreSQL and save the result
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO questions_answers (question, answer)
            VALUES (%s, %s)
            RETURNING id
            """,
            (request.question, answer)
        )

        question_id = cursor.fetchone()[0]

        connection.commit()

    except Exception:
        if connection:
            connection.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to store question and answer"
        )

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()

    # 3. Return structured response
    return {
        "question_id": question_id,
        "question": request.question,
        "answer": answer,
        "status": "success"
    }

@app.get("/answers/{question_id}", response_model=AnswerResponse)
def get_answer(question_id: int):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, question, answer
            FROM questions_answers
            WHERE id = %s
            """,
            (question_id,)
        )

        result = cursor.fetchone()

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Question and answer not found"
            )

        return {
            "question_id": result[0],
            "question": result[1],
            "answer": result[2],
            "status": "success"
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve question and answer"
        )

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()