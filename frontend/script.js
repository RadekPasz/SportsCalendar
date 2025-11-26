document.addEventListener('DOMContentLoaded', function () {
    const calendarEl = document.getElementById('calendar');
    const eventsContainer = document.getElementById('events');
    const form = document.getElementById('eventForm');

    //Calendar
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        navLinks: true,
        events: []
    });

    calendar.render();

    //Events storage
    const events = [];

    function renderEventsList() {
        if (!eventsContainer) return;
        eventsContainer.innerHTML = '';
        if (events.length === 0) {
            eventsContainer.textContent = 'No events yet.';
            return;
        }

        const ul = document.createElement('ul');
        events.forEach((ev, idx) => {
            const li = document.createElement('li');
            const date = ev.start ? new Date(ev.start).toLocaleString() : 'Unknown date';
            const titleDiv = document.createElement('div');
            titleDiv.textContent = `${ev.title} — ${date}`;
            li.appendChild(titleDiv);
            if (ev.description) {
                const d = document.createElement('div');
                d.style.fontSize = '0.9em';
                d.style.color = '#555';
                d.textContent = ev.description;
                li.appendChild(d);
            }
            ul.appendChild(li);
        });
        eventsContainer.appendChild(ul);
    }

    const sportSelect = document.getElementById('sport');
    const venueSelect = document.getElementById('venue');

    async function fetchOptions() {
        try {
            const [sportsRes, venuesRes] = await Promise.all([
                fetch('/api/sports'),
                fetch('/api/venues')
            ]);

            if (!sportsRes.ok || !venuesRes.ok) throw new Error('Failed to fetch options');

            const sports = await sportsRes.json();
            const venues = await venuesRes.json();

            //Filling out the sports and venues scrolldown menus
            if (sportSelect) {
                sportSelect.innerHTML = '';
                sportSelect.appendChild(new Option('Select sport', ''));
                sports.forEach(s => sportSelect.appendChild(new Option(s.name, s.id)));
            }

            if (venueSelect) {
                venueSelect.innerHTML = '';
                venueSelect.appendChild(new Option('Select venue', ''));
                venues.forEach(v => venueSelect.appendChild(new Option(`${v.name} — ${v.city}`, v.id)));
            }
        } catch (err) {
            console.error('Error loading options:', err);
            const hint = (window.location.protocol === 'file:') ? 'Open via server (see README).' : 'Start backend at http://127.0.0.1:5000';
            if (sportSelect) sportSelect.innerHTML = `<option value="">(error) ${hint}</option>`;
            if (venueSelect) venueSelect.innerHTML = `<option value="">(error) ${hint}</option>`;
        }
    }

    //Take existing events from backend and add them to calendar and list
    async function fetchEvents() {
        try {
            const res = await fetch('/api/events');
            if (!res.ok) throw new Error('Failed to fetch events');
            const remoteEvents = await res.json();
            remoteEvents.forEach(re => {
                //Only add events that have a valid start
                if (re.start) {
                    const ev = { id: re.id, title: re.title, start: re.start, description: re.description };
                    calendar.addEvent(ev);
                    events.push(ev);
                }
            });
            renderEventsList();
        } catch (err) {
            console.warn('Could not load events from backend:', err);
        }
    }

        //Search handler
        const searchInput = document.getElementById('eventSearch');
        const searchBtn = document.getElementById('searchBtn');
        const searchResults = document.getElementById('searchResults');

        async function doSearch(q) {
            if (!q || q.trim() === '') {
                searchResults.innerHTML = '<p>Enter a search term.</p>';
                return;
            }
            try {
                searchResults.innerHTML = '<p>Searching…</p>';
                const res = await fetch('/api/events/search?q=' + encodeURIComponent(q));
                if (!res.ok) throw new Error('Search failed');
                const items = await res.json();
                if (!Array.isArray(items) || items.length === 0) {
                    searchResults.innerHTML = '<p>No results.</p>';
                    return;
                }
                const ul = document.createElement('ul');
                items.forEach(it => {
                    const li = document.createElement('li');
                    const date = it.start ? new Date(it.start).toLocaleString() : 'Unknown date';
                    li.textContent = `${it.title} — ${date}`;
                    if (it.description) {
                        const d = document.createElement('div');
                        d.style.fontSize = '0.9em';
                        d.style.color = '#555';
                        d.textContent = it.description;
                        li.appendChild(d);
                    }
                    li.tabIndex = 0;
                    li.addEventListener('click', () => {
                        if (it.start) {
                            calendar.gotoDate(it.start);
                        }
                        //Display details
                        alert(it.title + '\n' + (it.start || '') + (it.description ? ('\n' + it.description) : ''));
                    });
                    ul.appendChild(li);
                });
                searchResults.innerHTML = '';
                searchResults.appendChild(ul);
            } catch (err) {
                console.error('Search error', err);
                searchResults.innerHTML = '<p>Error running search.</p>';
            }
        }

        if (searchBtn) searchBtn.addEventListener('click', () => doSearch(searchInput.value));
        if (searchInput) searchInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); doSearch(searchInput.value); } });

    //Handle submit form
    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const date = document.getElementById('event_date').value;
            const time = document.getElementById('event_time').value;
            const sportSelectEl = document.getElementById('sport');
            const venueSelectEl = document.getElementById('venue');
            const sport_id = sportSelectEl ? sportSelectEl.value : '';
            const venue_id = venueSelectEl ? venueSelectEl.value : '';
            const sport = sportSelectEl ? sportSelectEl.selectedOptions[0].text : '';
            const venue = venueSelectEl ? venueSelectEl.selectedOptions[0].text : '';

            if (!date || !time) {
                alert('Please provide date and time');
                return;
            }
            if (!sport_id || !venue_id) {
                alert('Please choose a sport and a venue');
                return;
            }

            const iso = date + 'T' + time;
            const title = `${sport} @ ${venue}`;
            //Get optional description for POST
            const description = (document.getElementById('description') || {}).value || null;

            //POST to backend 
            fetch('/api/events', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    sport_id_foreignkey: sport_id,
                    venue_id_foreignkey: venue_id,
                    event_date: date,
                    event_time: time,
                    description: description
                })
            })
            .then(async res => {
                let payload = {};
                try { payload = await res.json(); } catch (e) {}
                if (!res.ok) throw new Error(payload.error || 'Failed to save event');
                //Add to calendar and list
                calendar.addEvent({ title, start: iso });
                events.push({ title, start: iso, description });
                renderEventsList();
                form.reset();
            })
            .catch(err => {
                alert('Could not save event: ' + (err.message || err));
            });
        });
    }

    //Load options
    fetchOptions();

    //Load existing events
    fetchEvents();

    renderEventsList();
});
