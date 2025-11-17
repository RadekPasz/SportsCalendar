from fastapi import APIRouter, Query, HTTPException
from backend.db import get_db
from typing import Optional, Tuple, List, Dict

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

#This fucnction builds the SQL query dynamically based on the provided key words. It's a helper for the next function. 
def _build_events_query(
    venue_name: Optional[str],
    participant_name: Optional[str]
) -> Tuple[str, List[str]]:

    base_query = """
        SELECT DISTINCT
            e.event_id,
            e.event_date,
            e.event_time,
            s.name AS sport,
            v.name AS venue
        FROM event e
        JOIN sport s ON e.sport_id = s.sport_id
        JOIN venue v ON e.venue_id = v.venue_id
    """
    
    where_clauses = []
    join_clauses = []
    query_params = []

    #Filter by Venue Name
    if venue_name:
        where_clauses.append("v.name LIKE ?")
        #Partial and/or case-insensitive matching
        query_params.append(f"%{venue_name}%") 

    #Filter by participant name
    if participant_name:
        #Add join for the event_participant table
        join_clauses.append("JOIN event_participant ep ON e.event_id = ep.event_id")
        where_clauses.append("ep.participant_name LIKE ?")
        query_params.append(f"%{participant_name}%")

    #Assemble the query
    full_query = base_query
    
    if join_clauses:
        full_query += " " + " ".join(join_clauses)
        
    if where_clauses:
        #all filter conditions combined 
        full_query += " WHERE " + " AND ".join(where_clauses)
        
    full_query += " ORDER BY e.event_date ASC;"

    return full_query, query_params

@router.get("/")
def get_events(
    venue_name: Optional[str] = Query(None, description="Filter by the venue's name"),
    participant_name: Optional[str] = Query(None, description="Filter by the participant's or team's name")
) -> List[Dict]:
    #Get the SQL query and parameters from the helper method
    query, params = _build_events_query(venue_name, participant_name)
    
    #Execute the query
    conn = get_db()
    try:
        events = conn.execute(query, tuple(params)).fetchall()
    except Exception as exc:
        print(f"Database query error: {exc}")
        raise HTTPException(status_code=500, detail="Error fetching data from the database.")

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