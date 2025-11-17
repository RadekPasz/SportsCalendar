from fastapi import APIRouter
from backend.db import get_db

router = APIRouter(prefix="/venues", tags=["Venues"])

@router.get("/")
def get_venues(): 
    conn = get_db()
    venues = conn.execute("""
        SELECT
            v.venue_id,
            v.name,
            v.city,
            v.address
        FROM venue v
        ORDER BY v.name ASC;
    """).fetchall()

    return [dict(row) for row in venues]