const API_BASE = "http://127.0.0.1:8000";

//Load events when the page loads
document.addEventListener("DOMContentLoaded", loadEvents);

async function loadEvents() {
    const container = document.getElementById("events");
    container.innerHTML = "Loading events...";

    try {
        const res = await fetch(`${API_BASE}/events`);
        const events = await res.json();

        container.innerHTML = "";

        events.forEach(e => {
            const card = document.createElement("div");
            card.className = "event-card";

            card.innerHTML = `
                <h3>${e.sport}</h3>
                <p><strong>Date:</strong> ${e.event_date}</p>
                <p><strong>Time:</strong> ${e.event_time}</p>
                <p><strong>Venue:</strong> ${e.venue}</p>
            `;

            container.appendChild(card);
        });

    } catch (err) {
        container.innerHTML = "Error loading events.";
        console.error(err);
    }
}

const form = document.getElementById("eventForm");

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const event = {
        event_date: document.getElementById("event_date").value,
        event_time: document.getElementById("event_time").value,
        venue_id: Number(document.getElementById("venue_id").value),
        sport_id: Number(document.getElementById("sport_id").value),
        status: document.getElementById("status").value
    };

    const res = await fetch(`${API_BASE}/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(event)
    });

    if (res.ok) {
        alert("Event added successfully!");
        loadEvents();
    } else {
        alert("Error adding event.");
    }
});
