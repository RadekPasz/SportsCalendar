from fastapi import FastAPI
from backend.routers import events, teams, venues

app = FastAPI()

app.include_router(events.router)
app.include_router(teams.router)
app.include_router(venues.router)