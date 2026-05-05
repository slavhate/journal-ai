from fastapi import APIRouter, HTTPException, Path
from backend.markdown_service import read_md_file, list_available_dates

router = APIRouter(prefix="/api/days", tags=["days"])


@router.get("")
async def get_available_days():
    return list_available_dates()


@router.get("/{date}")
async def get_day_content(date: str = Path(..., pattern=r"^\d{4}-\d{2}-\d{2}$")):
    content = read_md_file(date)
    if not content:
        raise HTTPException(status_code=404, detail="No entries for this date")
    return {"date": date, "content": content}
