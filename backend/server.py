from flask import Flask, jsonify, send_from_directory
import sqlite3
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(APP_DIR, '..'))
# Prefer an existing 'sports.db' if present (user data), otherwise use 'app.db'
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


@app.route('/api/events')
def api_events():
    conn = get_db_connection()
    cur = conn.cursor()
    # Join with sport and venue to get readable names
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
        # Ensure time has seconds if missing
        if time and len(time.split(':')) == 2:
            time = time + ':00'
        start = f"{date}T{time}" if date and time else None
        title = f"{r['sport_name']} @ {r['venue_name']}"
        events.append({'id': r['event_id'], 'sport_id': r['sport_id'], 'venue_id': r['venue_id'], 'title': title, 'start': start})

    return jsonify(events)


@app.route('/<path:filename>')
def static_files(filename):
    # Serve frontend files for convenience
    return send_from_directory(app.static_folder, filename)


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    print('Starting backend on http://127.0.0.1:5000')
    app.run(debug=True)
