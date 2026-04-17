from fastapi import APIRouter
from sqlalchemy import text
from core.database import engine

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "Enterprise AI Platform Running"}

@router.get("/health/db")
def db_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"database": "connected"}
    except Exception:
        return {"database": "error"}