from flask import Flask, jsonify, send_from_directory, request
import sqlite3
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(APP_DIR, '..'))
DB_CANDIDATES = [os.path.join(ROOT, 'database', 'sports.db'), os.path.join(ROOT, 'database', 'app.db')]
DB_PATH = next((p for p in DB_CANDIDATES if os.path.exists(p)), DB_CANDIDATES[-1])
SCHEMA_PATH = os.path.join(ROOT, 'database', 'schema.sql')

app = Flask(__name__, static_folder=os.path.join(ROOT, 'frontend'))


def get_db_connection():
    need_init = not os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if need_init and os.path.exists(SCHEMA_PATH):
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()
    return conn


@app.route('/api/sports')
def api_sports():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT sport_id, name FROM sport ORDER BY name')
    rows = cur.fetchall()
    conn.close()
    sports = [{'id': r['sport_id'], 'name': r['name']} for r in rows]
    return jsonify(sports)


@app.route('/api/venues')
def api_venues():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT venue_id, name, city FROM venue ORDER BY name')
    rows = cur.fetchall()
    conn.close()
    venues = [{'id': r['venue_id'], 'name': r['name'], 'city': r['city']} for r in rows]
    return jsonify(venues)


#Displaying events in the app
@app.route('/api/events', methods=['GET'])
def api_events():
    conn = get_db_connection()
    cur = conn.cursor()
    #Join with sport and venue
    cur.execute('''
        SELECT e.event_id, e.sport_id, e.venue_id, e.event_date, e.event_time,
               s.name as sport_name, v.name as venue_name
        FROM event e
        JOIN sport s ON e.sport_id = s.sport_id
        JOIN venue v ON e.venue_id = v.venue_id
        ORDER BY e.event_date, e.event_time
    ''')
    rows = cur.fetchall()
    conn.close()

    events = []
    for r in rows:
        date = r['event_date']
        time = r['event_time']
        start = f"{date}T{time}" if date and time else None
        title = f"{r['sport_name']} @ {r['venue_name']}"
        events.append({'id': r['event_id'], 'sport_id': r['sport_id'], 'venue_id': r['venue_id'], 'title': title, 'start': start})

    return jsonify(events)


@app.route('/api/events/search')
def api_events_search():
    q = (request.args.get('q') or '').strip()
    conn = get_db_connection()
    cur = conn.cursor()
    params = []
    if q == '':
        #Return empty list for empty query
        conn.close()
        return jsonify([])

    #Search by keywords
    like = f"%{q}%"
    try:
        cur.execute('''
            SELECT e.event_id, e.sport_id, e.venue_id, e.event_date, e.event_time,
                   s.name as sport_name, v.name as venue_name
            FROM event e
            JOIN sport s ON e.sport_id = s.sport_id
            JOIN venue v ON e.venue_id = v.venue_id
            WHERE s.name LIKE ? OR v.name LIKE ? OR e.event_date LIKE ? OR e.event_time LIKE ?
            ORDER BY e.event_date, e.event_time
        ''', (like, like, like, like))
        rows = cur.fetchall()
    except Exception as e:
        app.logger.exception('Error running search')
        conn.close()
        return jsonify({'error': str(e)}), 500
    conn.close()

    results = []
    for r in rows:
        date = r['event_date']
        time = r['event_time']
        if time and len(time.split(':')) == 2:
            time = time + ':00'
        start = f"{date}T{time}" if date and time else None
        title = f"{r['sport_name']} @ {r['venue_name']}"
        results.append({'id': r['event_id'], 'title': title, 'start': start, 'sport_id': r['sport_id'], 'venue_id': r['venue_id']})

    return jsonify(results)


@app.route('/api/events', methods=['POST'])
def add_event():
    data = request.get_json(force=True)
    sport_id = data.get('sport_id')
    venue_id = data.get('venue_id')
    event_date = data.get('event_date')
    event_time = data.get('event_time')
    if not (sport_id and venue_id and event_date and event_time):
        app.logger.warning('POST /api/events missing fields: %s', data)
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        sport_id = int(sport_id)
        venue_id = int(venue_id)
    except Exception:
        app.logger.warning('POST /api/events invalid IDs: %s %s', sport_id, venue_id)
        return jsonify({'error': 'Invalid sport_id or venue_id'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO event (sport_id, venue_id, event_date, event_time) VALUES (?, ?, ?, ?)',
                    (sport_id, venue_id, event_date, event_time))
        conn.commit()
        event_id = cur.lastrowid
        conn.close()
        app.logger.info('Inserted event id=%s', event_id)
        return jsonify({'event_id': event_id}), 201
    except Exception as e:
        app.logger.exception('POST /api/events DB error')
        return jsonify({'error': str(e)}), 500


@app.route('/<path:filename>')
def static_files(filename):
    #Serve frontend files for convenience
    return send_from_directory(app.static_folder, filename)


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    print('Starting backend on http://127.0.0.1:5000')
    app.run(debug=True)
