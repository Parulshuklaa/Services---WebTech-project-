# ServiceX Full Stack Marketplace

ServiceX is a local service marketplace prototype with a static frontend, a Python REST API, SQLite persistence, provider ranking, booking creation, and Indian rupee pricing.

## Highlights

- REST API for services, providers, bookings, and health checks
- SQLite database seeded with service and provider records
- Provider matching based on rating, distance, Indian rupee price, urgency, and availability
- Booking form connected to backend with a browser fallback for GitHub Pages
- No external Python packages required

## Why GitHub Pages looks frontend-only

GitHub Pages hosts static files only. It cannot run `backend/app.py`, Python, or SQLite. The project is still full stack because the backend code and REST API are in this repository and run locally or on a backend host.

To make the public GitHub Pages link use the real backend:

1. Deploy the backend as a web service.
2. Copy the deployed API URL.
3. Open the GitHub Pages frontend with `?api=YOUR_BACKEND_URL` once. The frontend stores that API URL in the browser.

Example:

```text
https://parulshuklaa.github.io/Services---WebTech-project-/?api=https://servicex-api.onrender.com
```

The backend is cloud-ready through `render.yaml`.

## Deploy backend on Render

1. Push this repository to GitHub.
2. Open Render and create a new Blueprint or Web Service from this repository.
3. Use these settings if Render asks manually:
   - Runtime: Python
   - Build command: leave blank
   - Start command: `python3 backend/app.py`
   - Health check path: `/api/health`
4. After deploy, open `/api/health` on the Render URL. It should return:

```json
{
  "status": "ok",
  "service": "ServiceX API"
}
```

5. Connect the frontend by opening GitHub Pages with:

```text
https://parulshuklaa.github.io/Services---WebTech-project-/?api=YOUR_RENDER_BACKEND_URL
```

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
