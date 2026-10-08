# ServiceX Full Stack Marketplace

ServiceX is a local service marketplace prototype with a static frontend, a Python REST API, SQLite persistence, provider ranking, and booking creation.

## Highlights

- REST API for services, providers, bookings, and health checks
- SQLite database seeded with service and provider records
- Provider matching based on rating, distance, price, urgency, and availability
- Booking form connected to backend with a browser fallback for GitHub Pages
- No external Python packages required

## Run locally

Start the backend:

```bash
python3 backend/app.py
```

Open the frontend:

```bash
python3 -m http.server 5500
```

Then visit:

```text
http://127.0.0.1:5500
```

## API routes

```text
GET  /api/health
GET  /api/services
GET  /api/providers
GET  /api/providers?service=plumber
GET  /api/bookings
POST /api/bookings
```

Example booking request:

```json
{
  "customer_name": "Parul",
  "service_id": "plumber",
  "location": "Greater Noida",
  "urgency": "high"
}
```

## Tech stack

HTML, CSS, JavaScript, Python, SQLite, REST APIs
