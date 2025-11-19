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
    else:
        # Migration: if existing DB lacks *_foreignkey columns, add them and copy values
        try:
            cur = conn.cursor()
            # Check event table columns
            cur.execute("PRAGMA table_info('event')")
            cols = [r[1] for r in cur.fetchall()]
            if 'sport_id_foreignkey' not in cols:
                cur.execute('ALTER TABLE event ADD COLUMN sport_id_foreignkey INTEGER')
            if 'venue_id_foreignkey' not in cols:
                cur.execute('ALTER TABLE event ADD COLUMN venue_id_foreignkey INTEGER')
            if 'description' not in cols:
                cur.execute('ALTER TABLE event ADD COLUMN description TEXT')
            # Copy existing values when possible
            if 'sport_id' in cols and 'sport_id_foreignkey' not in cols:
                # sport_id_foreignkey was just added; copy values
                cur.execute('UPDATE event SET sport_id_foreignkey = sport_id WHERE sport_id_foreignkey IS NULL')
            if 'venue_id' in cols and 'venue_id_foreignkey' not in cols:
                cur.execute('UPDATE event SET venue_id_foreignkey = venue_id WHERE venue_id_foreignkey IS NULL')

            # event_participant
            cur.execute("PRAGMA table_info('event_participant')")
            ep_cols = [r[1] for r in cur.fetchall()]
            if 'event_id_foreignkey' not in ep_cols:
                try:
                    cur.execute('ALTER TABLE event_participant ADD COLUMN event_id_foreignkey INTEGER')
                except Exception:
                    pass
            if 'team_id_foreignkey' not in ep_cols:
                try:
                    cur.execute('ALTER TABLE event_participant ADD COLUMN team_id_foreignkey INTEGER')
                except Exception:
                    pass
            if 'event_id' in ep_cols:
                cur.execute('UPDATE event_participant SET event_id_foreignkey = event_id WHERE event_id_foreignkey IS NULL')
            if 'team_id' in ep_cols:
                cur.execute('UPDATE event_participant SET team_id_foreignkey = team_id WHERE team_id_foreignkey IS NULL')

            conn.commit()
        except Exception:
            # If migration fails, proceed without raising to avoid breaking startup
            conn.rollback()
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
    # Join with sport and venue (use *_foreignkey columns)
    cur.execute('''
        SELECT e.event_id, e.sport_id_foreignkey as sport_id_foreignkey, e.venue_id_foreignkey as venue_id_foreignkey,
               e.event_date, e.event_time, e.description,
               s.name as sport_name, v.name as venue_name
        FROM event e
        JOIN sport s ON e.sport_id_foreignkey = s.sport_id
        JOIN venue v ON e.venue_id_foreignkey = v.venue_id
        ORDER BY e.event_date, e.event_time
    ''')
    rows = cur.fetchall()
    conn.close()

    events = []
    for r in rows:
        date = r['event_date']
        time = r['event_time']
        desc = r.get('description') if isinstance(r, dict) else r['description'] if 'description' in r.keys() else None
        if time and len(time.split(':')) == 2:
            time = time + ':00'
        start = f"{date}T{time}" if date and time else None
        title = f"{r['sport_name']} @ {r['venue_name']}"
        events.append({'id': r['event_id'], 'sport_id_foreignkey': r['sport_id_foreignkey'], 'venue_id_foreignkey': r['venue_id_foreignkey'], 'title': title, 'start': start, 'description': desc})

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
            SELECT e.event_id, e.sport_id_foreignkey as sport_id_foreignkey, e.venue_id_foreignkey as venue_id_foreignkey,
                   e.event_date, e.event_time, e.description,
                   s.name as sport_name, v.name as venue_name
            FROM event e
            JOIN sport s ON e.sport_id_foreignkey = s.sport_id
            JOIN venue v ON e.venue_id_foreignkey = v.venue_id
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
        desc = r.get('description') if isinstance(r, dict) else r['description'] if 'description' in r.keys() else None
        if time and len(time.split(':')) == 2:
            time = time + ':00'
        start = f"{date}T{time}" if date and time else None
        title = f"{r['sport_name']} @ {r['venue_name']}"
        results.append({'id': r['event_id'], 'title': title, 'start': start, 'sport_id_foreignkey': r['sport_id_foreignkey'], 'venue_id_foreignkey': r['venue_id_foreignkey'], 'description': desc})

    return jsonify(results)


@app.route('/api/events', methods=['POST'])
def add_event():
    data = request.get_json(force=True)
    # Accept either new names or legacy names
    sport_id = data.get('sport_id_foreignkey') or data.get('sport_id')
    venue_id = data.get('venue_id_foreignkey') or data.get('venue_id')
    event_date = data.get('event_date')
    event_time = data.get('event_time')
    description = data.get('description')
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
        # Determine which columns exist to support older/new DB schemas
        cur.execute("PRAGMA table_info('event')")
        cols = [r[1] for r in cur.fetchall()]
        # Build insert dynamically
        insert_cols = []
        insert_vals = []
        # If legacy columns exist, set them too to satisfy NOT NULL constraints on older DBs
        if 'sport_id' in cols:
            insert_cols.append('sport_id')
            insert_vals.append(sport_id)
        if 'sport_id_foreignkey' in cols:
            insert_cols.append('sport_id_foreignkey')
            insert_vals.append(sport_id)
        if 'venue_id' in cols:
            insert_cols.append('venue_id')
            insert_vals.append(venue_id)
        if 'venue_id_foreignkey' in cols:
            insert_cols.append('venue_id_foreignkey')
            insert_vals.append(venue_id)
        # date, time, description
        insert_cols.extend(['event_date', 'event_time'])
        insert_vals.extend([event_date, event_time])
        if 'description' in cols:
            insert_cols.append('description')
            insert_vals.append(description)

        placeholders = ','.join(['?'] * len(insert_cols))
        sql = f"INSERT INTO event ({','.join(insert_cols)}) VALUES ({placeholders})"
        cur.execute(sql, tuple(insert_vals))
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
