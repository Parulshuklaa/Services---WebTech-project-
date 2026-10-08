from __future__ import annotations

import json
import math
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "backend" / "servicex.db"


SERVICES = [
    ("plumber", "Plumber", 40),
    ("electrician", "Electrician", 45),
    ("tutor", "Tutor", 30),
    ("mechanic", "Mechanic", 50),
]

PROVIDERS = [
    ("Aarav Repairs", "plumber", 4.8, 2.1, 42, "available"),
    ("FixFlow Plumbing", "plumber", 4.5, 4.6, 36, "available"),
    ("VoltCare", "electrician", 4.9, 3.2, 46, "available"),
    ("BrightSpark Services", "electrician", 4.4, 6.0, 39, "busy"),
    ("LearnMate", "tutor", 4.7, 1.8, 32, "available"),
    ("Concept Coach", "tutor", 4.3, 5.4, 28, "available"),
    ("AutoAid", "mechanic", 4.8, 3.8, 54, "available"),
    ("QuickWheels", "mechanic", 4.2, 7.1, 47, "available"),
]


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS services (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                base_price INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS providers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                service_id TEXT NOT NULL,
                rating REAL NOT NULL,
                distance_km REAL NOT NULL,
                hourly_rate INTEGER NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (service_id) REFERENCES services(id)
            );

            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                service_id TEXT NOT NULL,
                location TEXT NOT NULL,
                urgency TEXT NOT NULL,
                provider_id INTEGER NOT NULL,
                estimated_price INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'confirmed',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (service_id) REFERENCES services(id),
                FOREIGN KEY (provider_id) REFERENCES providers(id)
            );
            """
        )
        db.executemany(
            "INSERT OR IGNORE INTO services (id, name, base_price) VALUES (?, ?, ?)",
            SERVICES,
        )
        db.executemany(
            """
            INSERT INTO providers (name, service_id, rating, distance_km, hourly_rate, status)
            SELECT ?, ?, ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM providers WHERE name = ? AND service_id = ?
            )
            """,
            [provider + (provider[0], provider[1]) for provider in PROVIDERS],
        )


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(row) for row in rows]


def provider_score(provider: sqlite3.Row, urgency: str) -> float:
    rating_score = provider["rating"] * 20
    distance_penalty = provider["distance_km"] * (5 if urgency == "high" else 3)
    price_penalty = provider["hourly_rate"] * 0.7
    availability_bonus = 12 if provider["status"] == "available" else -20
    return round(rating_score + availability_bonus - distance_penalty - price_penalty, 2)


def estimate_price(provider: sqlite3.Row, urgency: str) -> int:
    urgency_factor = 1.35 if urgency == "high" else 1
    distance_fee = provider["distance_km"] * 4
    return math.ceil((provider["hourly_rate"] + distance_fee) * urgency_factor)


def find_best_match(service_id: str, urgency: str) -> dict | None:
    with connect() as db:
        providers = db.execute(
            """
            SELECT providers.*, services.name AS service_name
            FROM providers
            JOIN services ON services.id = providers.service_id
            WHERE service_id = ?
            """,
            (service_id,),
        ).fetchall()

    if not providers:
        return None

    ranked = []
    for provider in providers:
        ranked.append(
            {
                **dict(provider),
                "match_score": provider_score(provider, urgency),
                "estimated_price": estimate_price(provider, urgency),
            }
        )
    ranked.sort(key=lambda item: item["match_score"], reverse=True)
    return ranked[0]


class ServiceXHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            return self.send_json({"status": "ok", "service": "ServiceX API"})
        if parsed.path == "/api/services":
            with connect() as db:
                services = db.execute("SELECT * FROM services ORDER BY name").fetchall()
            return self.send_json(rows_to_dicts(services))
        if parsed.path == "/api/providers":
            query = parse_qs(parsed.query)
            service_id = query.get("service", [None])[0]
            with connect() as db:
                if service_id:
                    rows = db.execute(
                        "SELECT * FROM providers WHERE service_id = ? ORDER BY rating DESC",
                        (service_id,),
                    ).fetchall()
                else:
                    rows = db.execute("SELECT * FROM providers ORDER BY rating DESC").fetchall()
            return self.send_json(rows_to_dicts(rows))
        if parsed.path == "/api/bookings":
            with connect() as db:
                rows = db.execute(
                    """
                    SELECT bookings.*, services.name AS service_name, providers.name AS provider_name
                    FROM bookings
                    JOIN services ON services.id = bookings.service_id
                    JOIN providers ON providers.id = bookings.provider_id
                    ORDER BY bookings.created_at DESC
                    """
                ).fetchall()
            return self.send_json(rows_to_dicts(rows))

        self.send_error(404, "Route not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/bookings":
            return self.send_error(404, "Route not found")

        payload = self.read_json()
        required = ["customer_name", "service_id", "location", "urgency"]
        missing = [field for field in required if not str(payload.get(field, "")).strip()]
        if missing:
            return self.send_json({"error": f"Missing fields: {', '.join(missing)}"}, 400)

        service_id = payload["service_id"]
        urgency = payload["urgency"]
        if urgency not in {"normal", "high"}:
            return self.send_json({"error": "Urgency must be normal or high"}, 400)

        match = find_best_match(service_id, urgency)
        if not match:
            return self.send_json({"error": "No provider found for this service"}, 404)

        with connect() as db:
            cursor = db.execute(
                """
                INSERT INTO bookings (
                    customer_name, service_id, location, urgency, provider_id, estimated_price
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["customer_name"].strip(),
                    service_id,
                    payload["location"].strip(),
                    urgency,
                    match["id"],
                    match["estimated_price"],
                ),
            )
            booking_id = cursor.lastrowid

        return self.send_json(
            {
                "booking_id": booking_id,
                "status": "confirmed",
                "match": match,
                "message": "Booking confirmed with the best available provider.",
            },
            201,
        )

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw_body = self.rfile.read(length).decode("utf-8")
        try:
            return json.loads(raw_body)
        except json.JSONDecodeError:
            return {}

    def send_json(self, payload: dict | list, status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_headers("application/json", len(body))
        self.wfile.write(body)

    def send_headers(self, content_type: str = "application/json", length: int = 0) -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        if length:
            self.send_header("Content-Length", str(length))
        self.end_headers()


def run() -> None:
    init_db()
    server = ThreadingHTTPServer(("127.0.0.1", 8000), ServiceXHandler)
    print("ServiceX API running at http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    run()
