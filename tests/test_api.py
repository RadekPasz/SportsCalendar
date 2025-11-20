import os
import sqlite3
import tempfile
import importlib.util
import json


def create_test_db(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    #Create a tables for test purposes
    cur.executescript(open(os.path.join('database', 'schema.sql'), 'r', encoding='utf-8').read())
    cur.execute("INSERT INTO sport (name) VALUES (?)", ('TestSport',))
    cur.execute("INSERT INTO venue (name, city, address) VALUES (?, ?, ?)", ('TestVenue', 'TestCity', 'Addr 1'))
    cur.execute("PRAGMA table_info('event')")
    cols = [r[1] for r in cur.fetchall()]
    if 'sport_id_foreignkey' in cols and 'venue_id_foreignkey' in cols:
        cur.execute("INSERT INTO event (sport_id_foreignkey, venue_id_foreignkey, event_date, event_time, description) VALUES (?,?,?,?,?)",
                    (1, 1, '2025-11-20', '12:00', 'Seed event'))
    else:
        cur.execute("INSERT INTO event (sport_id, venue_id, event_date, event_time) VALUES (?,?,?,?,?)" % (), (1, 1, '2025-11-20', '12:00'))
    conn.commit()
    conn.close()


def load_server_module(path_to_server):
    spec = importlib.util.spec_from_file_location('server', path_to_server)
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)
    return server


def test_endpoints(tmp_path):
    db_file = tmp_path / 'test.db'
    create_test_db(str(db_file))

    server = load_server_module(os.path.join('backend', 'server.py'))
    #Point server to test DB
    server.DB_PATH = str(db_file)

    client = server.app.test_client()

    #GET /api/sports - should return 200 and a non-empty list of sports
    r = client.get('/api/sports')
    assert r.status_code == 200
    sports = r.get_json()
    assert isinstance(sports, list)
    assert len(sports) >= 1

    #GET /api/venues - should return 200 and a non-empty list of venues
    r = client.get('/api/venues')
    assert r.status_code == 200
    venues = r.get_json()
    assert isinstance(venues, list)
    assert len(venues) >= 1

    #GET /api/events - should return 200 and at least one event with a start timestamp
    r = client.get('/api/events')
    assert r.status_code == 200
    events = r.get_json()
    assert isinstance(events, list)
    assert len(events) >= 1
    ev = events[0]
    #Each event must include a 'start' field
    assert 'start' in ev

    #POST /api/events - creating a new event should return 201 and include the new event_id
    payload = {
        'sport_id_foreignkey': 1,
        'venue_id_foreignkey': 1,
        'event_date': '2025-12-01',
        'event_time': '19:30',
        'description': 'Posted by test'
    }
    r = client.post('/api/events', data=json.dumps(payload), content_type='application/json')
    assert r.status_code == 201
    body = r.get_json()
    #Response must include the new event's id
    assert 'event_id' in body

    #GET /api/events/search?q= - searching by sport should return matching events
    r = client.get('/api/events/search?q=TestSport')
    assert r.status_code == 200
    results = r.get_json()
    assert isinstance(results, list)
    assert len(results) >= 1


def test_post_missing_fields_returns_400(tmp_path):
    db_file = tmp_path / 'test.db'
    create_test_db(str(db_file))
    server = load_server_module(os.path.join('backend', 'server.py'))
    server.DB_PATH = str(db_file)
    client = server.app.test_client()

    #POST with missing required fields should return 400 and an error message
    payload = {'sport_id_foreignkey': 1, 'venue_id_foreignkey': 1, 'event_date': '2025-12-01'}
    r = client.post('/api/events', data=json.dumps(payload), content_type='application/json')
    assert r.status_code == 400
    body = r.get_json()
    assert body and 'error' in body


def test_post_invalid_ids_returns_400(tmp_path):
    db_file = tmp_path / 'test.db'
    create_test_db(str(db_file))
    server = load_server_module(os.path.join('backend', 'server.py'))
    server.DB_PATH = str(db_file)
    client = server.app.test_client()

    #POST with non-numeric IDs should return 400 and an error message
    payload = {'sport_id_foreignkey': 'not-an-int', 'venue_id_foreignkey': 'x', 'event_date': '2025-12-01', 'event_time': '10:00'}
    r = client.post('/api/events', data=json.dumps(payload), content_type='application/json')
    assert r.status_code == 400
    body = r.get_json()
    assert body and 'error' in body


def test_search_empty_query_returns_empty_list(tmp_path):
    db_file = tmp_path / 'test.db'
    create_test_db(str(db_file))
    server = load_server_module(os.path.join('backend', 'server.py'))
    server.DB_PATH = str(db_file)
    client = server.app.test_client()

    #Empty search query returns 200 and an empty list
    r = client.get('/api/events/search?q=')
    assert r.status_code == 200
    body = r.get_json()
    assert isinstance(body, list) and len(body) == 0


def test_post_without_description_succeeds(tmp_path):
    db_file = tmp_path / 'test.db'
    create_test_db(str(db_file))
    server = load_server_module(os.path.join('backend', 'server.py'))
    server.DB_PATH = str(db_file)
    client = server.app.test_client()

    #Posting without a description is allowed; the server should still create the event
    payload = {'sport_id_foreignkey': 1, 'venue_id_foreignkey': 1, 'event_date': '2025-12-05', 'event_time': '18:00'}
    r = client.post('/api/events', data=json.dumps(payload), content_type='application/json')
    assert r.status_code == 201
    body = r.get_json()
    assert 'event_id' in body
