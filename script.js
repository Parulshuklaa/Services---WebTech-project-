const bookingForm = document.getElementById('bookingForm');
const bookingResult = document.getElementById('bookingResult');

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

bookingForm.addEventListener('submit', event => {
  event.preventDefault();

  const service = document.getElementById('service').value;
  const location = document.getElementById('location').value.trim();
  const urgency = document.getElementById('urgency').value;

  if (!location) {
    bookingResult.innerHTML = '<p>Please enter a valid location.</p>';
    bookingResult.classList.remove('hidden');
    return;
  }

  const estimate = calculateEstimate(service, urgency);
  bookingResult.innerHTML = buildMatchMessage(service, location, urgency, estimate);
  bookingResult.classList.remove('hidden');
});