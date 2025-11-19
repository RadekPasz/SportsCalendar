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
    sport_id_foreignkey INTEGER NOT NULL,
    venue_id_foreignkey INTEGER NOT NULL,
    description TEXT,
    event_date DATE NOT NULL,
    event_time TIME NOT NULL,
    FOREIGN KEY (sport_id_foreignkey) REFERENCES sport(sport_id),
    FOREIGN KEY (venue_id_foreignkey) REFERENCES venue(venue_id)
);

CREATE TABLE team (
    team_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE event_participant (
    event_id_foreignkey INTEGER NOT NULL,
    participant_name TEXT NOT NULL,
    team_id_foreignkey INTEGER NOT NULL,
    PRIMARY KEY (event_id_foreignkey, participant_name),
    FOREIGN KEY (event_id_foreignkey) REFERENCES event(event_id),
    FOREIGN KEY (team_id_foreignkey) REFERENCES team(team_id)
);