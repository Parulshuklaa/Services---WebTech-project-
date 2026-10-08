const bookingForm = document.getElementById('bookingForm');
const bookingResult = document.getElementById('bookingResult');
const bookingList = document.getElementById('bookingList');
const apiStatus = document.getElementById('apiStatus');
const API_BASE = 'http://127.0.0.1:8000';

const pricing = {
  plumber: 40,
  electrician: 45,
  tutor: 30,
  mechanic: 50,
};

function calculateEstimate(service, urgency) {
  const base = pricing[service] || 40;
  const demandFactor = urgency === 'high' ? 1.35 : 1;
  const distanceFactor = 1 + Math.random() * 0.25;
  return Math.round(base * distanceFactor * demandFactor);
}

function buildMatchMessage(service, location, urgency, estimate) {
  return `
    <h3>Match Ready</h3>
    <p><strong>Service:</strong> ${service.charAt(0).toUpperCase() + service.slice(1)}</p>
    <p><strong>Location:</strong> ${location}</p>
    <p><strong>Urgency:</strong> ${urgency === 'high' ? 'High demand' : 'Normal'}</p>
    <p><strong>Estimated Price:</strong> $${estimate}</p>
    <p>Provider score is computed from rating, distance, and price to deliver the best local match.</p>
  `;
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Request failed');
  }
  return data;
}

function buildBackendMatchMessage(result, service, location, urgency) {
  const match = result.match;
  return `
    <h3>Booking Confirmed</h3>
    <p><strong>Booking ID:</strong> #${result.booking_id}</p>
    <p><strong>Service:</strong> ${service.charAt(0).toUpperCase() + service.slice(1)}</p>
    <p><strong>Location:</strong> ${location}</p>
    <p><strong>Urgency:</strong> ${urgency === 'high' ? 'High demand' : 'Normal'}</p>
    <p><strong>Provider:</strong> ${match.name} (${match.rating}/5 rating, ${match.distance_km} km away)</p>
    <p><strong>Estimated Price:</strong> $${match.estimated_price}</p>
    <p><strong>Match Score:</strong> ${match.match_score}</p>
  `;
}

async function loadBookings() {
  try {
    const bookings = await apiRequest('/api/bookings');
    bookingList.innerHTML = bookings.length
      ? bookings.slice(0, 5).map(booking => `
          <li>
            <strong>#${booking.id}</strong> ${booking.service_name} with ${booking.provider_name}
            <span>${booking.status} • $${booking.estimated_price}</span>
          </li>
        `).join('')
      : '<li>No bookings yet. Create the first one.</li>';
    apiStatus.textContent = 'Connected to Python + SQLite backend.';
  } catch (error) {
    apiStatus.textContent = 'Backend offline. Demo mode is using frontend-only matching.';
    bookingList.innerHTML = '<li>Start backend/app.py to persist bookings.</li>';
  }
}

bookingForm.addEventListener('submit', event => {
  event.preventDefault();

  const customerName = document.getElementById('customerName').value.trim();
  const service = document.getElementById('service').value;
  const location = document.getElementById('location').value.trim();
  const urgency = document.getElementById('urgency').value;

  if (!customerName || !location) {
    bookingResult.innerHTML = '<p>Please enter your name and a valid location.</p>';
    bookingResult.classList.remove('hidden');
    return;
  }

  apiRequest('/api/bookings', {
    method: 'POST',
    body: JSON.stringify({
      customer_name: customerName,
      service_id: service,
      location,
      urgency,
    }),
  })
    .then(result => {
      bookingResult.innerHTML = buildBackendMatchMessage(result, service, location, urgency);
      bookingResult.classList.remove('hidden');
      return loadBookings();
    })
    .catch(() => {
      const estimate = calculateEstimate(service, urgency);
      bookingResult.innerHTML = buildMatchMessage(service, location, urgency, estimate);
      bookingResult.classList.remove('hidden');
    });
});

loadBookings();
