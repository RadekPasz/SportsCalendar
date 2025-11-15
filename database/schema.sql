CREATE TABLE sport (
    sport_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE venue (
    venue_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    city TEXT NOT NULL, 
    address TEXT NOT NULL
);

CREATE TABLE event (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport_id INTEGER NOT NULL,
    venue_id INTEGER NOT NULL,
    event_date DATE NOT NULL,
    event_time TIME NOT NULL,
    FOREIGN KEY (sport_id) REFERENCES sport(sport_id),
    FOREIGN KEY (venue_id) REFERENCES venue(venue_id)
);

CREATE TABLE team (
    team_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE event_participant (
    event_id INTEGER NOT NULL,
    participant_name TEXT NOT NULL,
    team_id INTEGER NOT NULL,
    PRIMARY KEY (event_id, participant_name),
    FOREIGN KEY (event_id) REFERENCES event(event_id),
    FOREIGN KEY (team_id) REFERENCES team(team_id)
);