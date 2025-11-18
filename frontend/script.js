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
            li.textContent = `${ev.title} — ${date}`;
            ul.appendChild(li);
        });
        eventsContainer.appendChild(ul);
    }

    // Populate sport and venue selects from backend API
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

            // Populate sport select
            if (sportSelect) {
                sportSelect.innerHTML = '';
                sportSelect.appendChild(new Option('Select sport', ''));
                sports.forEach(s => sportSelect.appendChild(new Option(s.name, s.id)));
            }

            // Populate venue select
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

    // Fetch existing events from backend and add them to calendar/list
    async function fetchEvents() {
        try {
            const res = await fetch('/api/events');
            if (!res.ok) throw new Error('Failed to fetch events');
            const remoteEvents = await res.json();
            remoteEvents.forEach(re => {
                // Only add events that have a valid start
                if (re.start) {
                    const ev = { id: re.id, title: re.title, start: re.start };
                    calendar.addEvent(ev);
                    events.push(ev);
                }
            });
            renderEventsList();
        } catch (err) {
            console.warn('Could not load events from backend:', err);
            // keep the local list as-is; user can still add events manually
        }
    }

    // Handle form submit using sport and venue names
    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const date = document.getElementById('event_date').value;
            const time = document.getElementById('event_time').value;
            const sportSelectEl = document.getElementById('sport');
            const venueSelectEl = document.getElementById('venue');
            const sport = sportSelectEl ? sportSelectEl.selectedOptions[0].text : '';
            const venue = venueSelectEl ? venueSelectEl.selectedOptions[0].text : '';
            const status = document.getElementById('status').value || 'scheduled';

            if (!date || !time) {
                alert('Please provide date and time');
                return;
            }
            if (!sport || !venue) {
                alert('Please choose a sport and a venue');
                return;
            }

            const iso = date + 'T' + time;
            const title = `${sport} @ ${venue} (${status})`;
            const newEvent = { title: title, start: iso };

            calendar.addEvent(newEvent);
            events.push(newEvent);
            renderEventsList();

            form.reset();
            if (document.getElementById('status')) document.getElementById('status').value = 'scheduled';
        });
    }

    // Load options from backend
    fetchOptions();

    // Load existing events
    fetchEvents();

    renderEventsList();
});
