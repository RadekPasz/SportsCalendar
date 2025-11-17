from fastapi import APIRouter
from backend.db import get_db

router = APIRouter(prefix="/events", tags=["Events"])

@router.get("/")
def get_events():
    conn = get_db()
    events = conn.execute("""
        SELECT
            e.event_id,
            e.event_date,
            e.event_time,
            s.name as sport,
            v.name as venue
        FROM event e
        JOIN sport s ON e.sport_id = s.sport_id
        JOIN venue v ON e.venue_id = v.venue_id
        ORDER BY e.event_date ASC;
    """).fetchall()

    return [dict(row) for row in events]


@router.get("/{event_id}")
def get_event(event_id: int):
    conn = get_db()

    event = conn.execute("""
        SELECT
            e.*,
            s.name AS sport,
            v.name AS venue
        FROM event e
        JOIN sport s ON e.sport_id = s.sport_id
        JOIN venue v ON e.venue_id = v.venue_id
        WHERE e.event_id = ?
    """, (event_id,)).fetchone()

    participants = conn.execute("""
        SELECT participant_name
        FROM event_participant
        WHERE event_id = ?
    """, (event_id,)).fetchall()

    return {
        "event": dict(event),
        "participants": [p["participant_name"] for p in participants]
    }

@router.post("/")
def create_event(event: dict):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO event (sport_id, venue_id, event_date, event_time, description)
        VALUES (?, ?, ?, ?, ?)
    """, (
        event["sport_id"],
        event["venue_id"],
        event["event_date"],
        event["event_time"],
        event.get("description", None)
    ))
    event_id = cursor.lastrowid

    for participant in event.get("participants", []):
        cursor.execute("""
            INSERT INTO event_participant (event_id, participant_name)
            VALUES (?, ?)
        """, (event_id, participant))

    conn.commit()
    return {"event_id": event_id}