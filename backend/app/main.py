
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import get_db
from app.services.classifier import classify_question
from app.services.query_service import QUERIES, execute_query

app = FastAPI(
    title="Flight Deck API",
    description="AI-powered business query and decision support prototype",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class AskRequest(BaseModel):
    question: str


@app.get("/")
def root():
    return {
        "message": "Flight Deck API is running",
        "status": "healthy",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/questions")
def list_questions():
    return [
        {
            "query_id": query_id,
            "question": details["question"],
        }
        for query_id, details in QUERIES.items()
    ]


@app.post("/ask")
def ask_question(request: AskRequest, db: Session = Depends(get_db)):
    classification = classify_question(request.question)
    query_id = classification["query_id"]

    if not query_id:
        return {
            "status": "not_recognized",
            "message": "I couldn't match that question to an approved business query yet. Try asking about sales pipeline, top deals, quarterly revenue, monthly revenue trends, pending billing, or overdue billing.",
            "data": [],
        }

    try:
        result = execute_query(db, query_id)
        return {
            "status": "success",
            "recognized_query": query_id,
            "confidence": classification["confidence"],
            **result,
        }
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed for {query_id}. Check the query mapping and database schema.",
        ) from error
