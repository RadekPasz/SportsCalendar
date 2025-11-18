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

    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const date = document.getElementById('event_date').value;
            const time = document.getElementById('event_time').value;
            const sport_id = document.getElementById('sport_id').value;
            const venue_id = document.getElementById('venue_id').value;
            const status = document.getElementById('status').value || 'scheduled';

            if (!date || !time) {
                alert('Please provide date and time');
                return;
            }

            const iso = date + 'T' + time;
            const title = `Sport ${sport_id} @ Venue ${venue_id} (${status})`;
            const newEvent = { title: title, start: iso };

            calendar.addEvent(newEvent);
            events.push(newEvent);
            renderEventsList();

            form.reset();
            document.getElementById('status').value = 'scheduled';
        });
    }

    renderEventsList();
});
