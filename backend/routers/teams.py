from fastapi import APIRouter
from backend.db import get_db

router = APIRouter(prefix="/teams", tags=["Teams"])

@router.get("/") 
def get_teams():
    conn = get_db()
    teams = conn.execute("""
        SELECT
            t.team_id,
            t.name
        FROM team t
        ORDER BY t.name ASC;
    """).fetchall()

    return [dict(row) for row in teams]