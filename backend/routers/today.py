from fastapi import APIRouter
from datetime import date
from backend.database import get_events_by_date, get_upcoming_todos

router = APIRouter(tags=["today"])


@router.get("/api/today")
async def get_today_events():
    today = date.today().isoformat()
    return get_events_by_date(today)


@router.get("/api/todos")
async def get_todos():
    return get_upcoming_todos()
