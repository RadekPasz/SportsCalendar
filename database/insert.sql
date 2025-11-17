INSERT INTO sport (name) VALUES ('Football');
INSERT INTO sport (name) VALUES ('Ice Hockey');
INSERT INTO sport (name) VALUES ('Basketball');
INSERT INTO sport (name) VALUES ('Tennis');
INSERT INTO sport (name) VALUES ('Volleyball');

INSERT INTO venue (name, city, address) VALUES
('Red Bull Arena', 'Salzburg', 'Stadionstraße 2'),
('Stadthalle', 'Klagenfurt', 'Messeplatz 1'),
('Wörthersee Stadion', 'Klagenfurt', 'Friedrich-Engels-Straße 1'),
('Tennis Club Wien', 'Vienna', 'Heinrich-Collin-Straße 30'),
('Volleyball Arena', 'Graz', 'Sportplatzgasse 5');

INSERT INTO team (name) VALUES 
('Salzburg'),
('Sturm'),
('Rapid Wien'),
('Vienna'),
('Graz');

INSERT INTO event (event_date, event_time, venue_id, sport_id)
VALUES ('2025-07-18', '18:30', 1, 1);
INSERT INTO event (event_date, event_time, venue_id, sport_id)
VALUES ('2025-10-23', '09:45', 2, 2);

INSERT INTO event_participant (event_id, participant_name, team_id) VALUES
(1, 'Salzburg', 1),
(1, 'Sturm', 2);
INSERT INTO event_participant (event_id, participant_name, team_id) VALUES
(2, 'KAC', 3),
(2, 'Capitals', 4);