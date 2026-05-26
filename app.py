import os
import re
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_PATH = os.path.join(BASE_DIR, "bristol_buzz.db")
EMAIL_PATTERN = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)
MAX_TICKETS_PER_BOOKING = 6

EVENT_SEED_DATA = [
    {
        "category_name": "Family Friendly",
        "category_description": "Events suitable for families and visitors of all ages.",
        "venue_name": "Ashton Court Estate",
        "address_line": "Long Ashton",
        "city": "Bristol",
        "postcode": "BS41 9JN",
        "map_url": "https://www.google.com/maps?q=Ashton+Court+Estate,+Long+Ashton,+Bristol+BS41+9JN",
        "event_title": "International Balloon Fiesta",
        "event_description": "Europe's largest annual meeting of hot air balloons.",
        "event_date": "2026-08-07",
        "start_time": "18:00:00",
        "price_label": "Free entry",
        "image_url": "assets/events/balloon-fiesta.jfif",
    },
    {
        "category_name": "Music",
        "category_description": "Concerts, festivals, and live music events.",
        "venue_name": "Bristol Harbourside",
        "address_line": "Harbourside",
        "city": "Bristol",
        "postcode": "BS1 5DB",
        "map_url": "https://www.google.com/maps?q=Bristol+Harbour,+Bristol",
        "event_title": "Love Saves The Day",
        "event_description": "A Bristol music festival with national and local performers.",
        "event_date": "2026-05-23",
        "start_time": "12:00:00",
        "price_label": "Tickets live",
        "image_url": "assets/events/music-festival.jfif",
    },
    {
        "category_name": "Arts and Culture",
        "category_description": "Theatre, opera, light shows, and cultural activities.",
        "venue_name": "Bristol City Centre",
        "address_line": "Broadmead and Old City",
        "city": "Bristol",
        "postcode": "BS1 1HQ",
        "map_url": "https://www.google.com/maps?q=Bristol+City+Centre",
        "event_title": "Bristol Light Festival",
        "event_description": "A winter evening light trail with glowing installations and family-friendly walking routes.",
        "event_date": "2026-11-27",
        "start_time": "17:30:00",
        "price_label": "Free trail",
        "image_url": "assets/events/light-festival.jfif",
    },
    {
        "category_name": "Arts and Culture",
        "category_description": "Theatre, opera, light shows, and cultural activities.",
        "venue_name": "Bristol Hippodrome",
        "address_line": "St Augustine's Parade",
        "city": "Bristol",
        "postcode": "BS1 4UZ",
        "map_url": "https://www.google.com/maps?q=Bristol+Hippodrome,+St+Augustine%27s+Parade,+Bristol+BS1+4UZ",
        "event_title": "Opera: La Boheme",
        "event_description": "Puccini opera performance with English surtitles.",
        "event_date": "2026-06-19",
        "start_time": "19:30:00",
        "price_label": "Ticketed",
        "image_url": "assets/events/opera.jfif",
    },
    {
        "category_name": "Food and Drink",
        "category_description": "Food markets, tasting events, and local produce festivals.",
        "venue_name": "Bristol Harbourside",
        "address_line": "Harbourside",
        "city": "Bristol",
        "postcode": "BS1 5DB",
        "map_url": "https://www.google.com/maps?q=Bristol+Harbour,+Bristol",
        "event_title": "Bristol Food Festival",
        "event_description": "Street food, cooking demonstrations, and local producers around the harbour.",
        "event_date": "2026-07-11",
        "start_time": "11:00:00",
        "price_label": "Food and drink",
        "image_url": "assets/events/food-festival.jfif",
    },
    {
        "category_name": "Arts and Culture",
        "category_description": "Theatre, opera, light shows, and cultural activities.",
        "venue_name": "Theatre Royal Bristol",
        "address_line": "King Street",
        "city": "Bristol",
        "postcode": "BS1 4ED",
        "map_url": "https://www.google.com/maps?q=The+Theatre+Royal,+Bristol",
        "event_title": "Bristol Comedy Festival",
        "event_description": "Stand-up comedy featuring established comedians and Bristol talent.",
        "event_date": "2026-08-22",
        "start_time": "19:30:00",
        "price_label": "Comedy night",
        "image_url": "assets/events/comedy-night.jfif",
    },
    {
        "category_name": "Sport",
        "category_description": "Running, fitness, and competitive community events.",
        "venue_name": "Millennium Square",
        "address_line": "Explore Lane",
        "city": "Bristol",
        "postcode": "BS1 5SZ",
        "map_url": "https://www.google.com/maps?q=Millennium+Square,+Bristol",
        "event_title": "Great Bristol Half Marathon",
        "event_description": "A city running event with half marathon and 10k options.",
        "event_date": "2026-05-10",
        "start_time": "09:00:00",
        "price_label": "Registration required",
        "image_url": "assets/events/half-marathon.jfif",
    },
]


def load_local_env():
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        return

    with open(env_path, encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            if key:
                os.environ.setdefault(key, value)


load_local_env()


def get_secret_key():
    configured_key = os.getenv("FLASK_SECRET_KEY", "").strip()
    if configured_key and configured_key != "change-this-dev-secret":
        return configured_key

    if os.getenv("FLASK_ENV") == "production":
        raise RuntimeError("FLASK_SECRET_KEY must be set in production.")

    return secrets.token_urlsafe(32)


app = Flask(__name__, template_folder=BASE_DIR)
app.secret_key = get_secret_key()
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "").lower() == "true",
)


PAGES = {
    "/": "BristolBuzz.html",
    "/BristolBuzz.html": "BristolBuzz.html",
    "/events": "events.html",
    "/events.html": "events.html",
    "/account": "account.html",
    "/account.html": "account.html",
    "/ticket": "ticket.html",
    "/ticket.html": "ticket.html",
    "/curator": "curator.html",
    "/curator.html": "curator.html",
    "/disclaimer": "disclaimer.html",
    "/disclaimer.html": "disclaimer.html",
    "/privacy-policy": "privacy-policy.html",
    "/privacy-policy.html": "privacy-policy.html",
    "/terms-of-service": "terms-of-service.html",
    "/terms-of-service.html": "terms-of-service.html",
}


def using_mysql():
    return os.getenv("DB_BACKEND", "").lower() == "mysql" or bool(os.getenv("MYSQL_HOST"))


def get_db_connection():
    if using_mysql():
        import mysql.connector

        return mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "bristol_buzz"),
        )

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def execute(cursor, query, values=None):
    if values is None:
        values = ()
    if using_mysql():
        query = query.replace("?", "%s")
    cursor.execute(query, values)


def init_db():
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        if using_mysql():
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS categories (
                    category_id INT AUTO_INCREMENT PRIMARY KEY,
                    category_name VARCHAR(80) NOT NULL UNIQUE,
                    category_description VARCHAR(255)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS venues (
                    venue_id INT AUTO_INCREMENT PRIMARY KEY,
                    venue_name VARCHAR(120) NOT NULL,
                    address_line VARCHAR(160) NOT NULL,
                    city VARCHAR(80) NOT NULL DEFAULT 'Bristol',
                    postcode VARCHAR(12) NOT NULL,
                    map_url VARCHAR(500),
                    UNIQUE (venue_name, postcode)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    event_id INT AUTO_INCREMENT PRIMARY KEY,
                    category_id INT NOT NULL,
                    venue_id INT NOT NULL,
                    event_title VARCHAR(160) NOT NULL UNIQUE,
                    event_description TEXT NOT NULL,
                    event_date DATE NOT NULL,
                    start_time TIME NOT NULL,
                    price_label VARCHAR(60) NOT NULL,
                    image_url VARCHAR(500),
                    CONSTRAINT fk_events_category
                        FOREIGN KEY (category_id) REFERENCES categories(category_id)
                        ON UPDATE CASCADE ON DELETE RESTRICT,
                    CONSTRAINT fk_events_venue
                        FOREIGN KEY (venue_id) REFERENCES venues(venue_id)
                        ON UPDATE CASCADE ON DELETE RESTRICT
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS bookings (
                    booking_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    event_id INT NOT NULL,
                    attendee_name VARCHAR(120) NOT NULL DEFAULT '',
                    attendee_email VARCHAR(255) NOT NULL DEFAULT '',
                    attendee_phone VARCHAR(30),
                    ticket_quantity INT NOT NULL DEFAULT 1,
                    special_requests VARCHAR(500),
                    booking_status VARCHAR(30) NOT NULL DEFAULT 'confirmed',
                    payment_status VARCHAR(30) NOT NULL DEFAULT 'accepted',
                    payment_reference VARCHAR(40) UNIQUE,
                    booked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_bookings_user
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                        ON DELETE CASCADE,
                    CONSTRAINT fk_bookings_event
                        FOREIGN KEY (event_id) REFERENCES events(event_id)
                        ON DELETE RESTRICT
                )
                """
            )
        else:
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS categories (
                    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_name TEXT NOT NULL UNIQUE,
                    category_description TEXT
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS venues (
                    venue_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venue_name TEXT NOT NULL,
                    address_line TEXT NOT NULL,
                    city TEXT NOT NULL DEFAULT 'Bristol',
                    postcode TEXT NOT NULL,
                    map_url TEXT,
                    UNIQUE (venue_name, postcode)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    venue_id INTEGER NOT NULL,
                    event_title TEXT NOT NULL UNIQUE,
                    event_description TEXT NOT NULL,
                    event_date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    price_label TEXT NOT NULL,
                    image_url TEXT,
                    FOREIGN KEY (category_id) REFERENCES categories(category_id)
                        ON UPDATE CASCADE ON DELETE RESTRICT,
                    FOREIGN KEY (venue_id) REFERENCES venues(venue_id)
                        ON UPDATE CASCADE ON DELETE RESTRICT
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS bookings (
                    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    event_id INTEGER NOT NULL,
                    attendee_name TEXT NOT NULL DEFAULT '',
                    attendee_email TEXT NOT NULL DEFAULT '',
                    attendee_phone TEXT,
                    ticket_quantity INTEGER NOT NULL DEFAULT 1,
                    special_requests TEXT,
                    booking_status TEXT NOT NULL DEFAULT 'confirmed',
                    payment_status TEXT NOT NULL DEFAULT 'accepted',
                    payment_reference TEXT UNIQUE,
                    booked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (event_id) REFERENCES events(event_id)
                        ON DELETE RESTRICT
                )
                """
            )

        ensure_booking_columns(cursor)
        seed_events(cursor)
        conn.commit()


def ensure_booking_columns(cursor):
    if using_mysql():
        cursor.execute("SHOW COLUMNS FROM bookings")
        existing = {row[0] for row in cursor.fetchall()}
        column_definitions = {
            "attendee_name": "VARCHAR(120) NOT NULL DEFAULT ''",
            "attendee_email": "VARCHAR(255) NOT NULL DEFAULT ''",
            "attendee_phone": "VARCHAR(30)",
            "ticket_quantity": "INT NOT NULL DEFAULT 1",
            "special_requests": "VARCHAR(500)",
            "payment_status": "VARCHAR(30) NOT NULL DEFAULT 'accepted'",
            "payment_reference": "VARCHAR(40)",
        }
    else:
        cursor.execute("PRAGMA table_info(bookings)")
        existing = {row[1] for row in cursor.fetchall()}
        column_definitions = {
            "attendee_name": "TEXT NOT NULL DEFAULT ''",
            "attendee_email": "TEXT NOT NULL DEFAULT ''",
            "attendee_phone": "TEXT",
            "ticket_quantity": "INTEGER NOT NULL DEFAULT 1",
            "special_requests": "TEXT",
            "payment_status": "TEXT NOT NULL DEFAULT 'accepted'",
            "payment_reference": "TEXT",
        }

    add_missing_columns(cursor, "bookings", existing, column_definitions)


def add_missing_columns(cursor, table_name, existing_columns, column_definitions):
    safe_tables = {"bookings"}
    if table_name not in safe_tables:
        raise ValueError("Unsupported table migration.")

    for column, definition in column_definitions.items():
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", column):
            raise ValueError(f"Unsafe column name: {column}")
        if column not in existing_columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column} {definition}")


def seed_events(cursor):
    for event in EVENT_SEED_DATA:
        category_id = upsert_category(
            cursor,
            event["category_name"],
            event["category_description"],
        )
        venue_id = upsert_venue(
            cursor,
            event["venue_name"],
            event["address_line"],
            event["city"],
            event["postcode"],
            event["map_url"],
        )
        upsert_event(cursor, event, category_id, venue_id)


def upsert_category(cursor, name, description):
    execute(cursor, "SELECT category_id FROM categories WHERE category_name = ?", (name,))
    row = cursor.fetchone()
    if row:
        execute(
            cursor,
            "UPDATE categories SET category_description = ? WHERE category_id = ?",
            (description, row[0]),
        )
        return row[0]

    execute(
        cursor,
        "INSERT INTO categories (category_name, category_description) VALUES (?, ?)",
        (name, description),
    )
    execute(cursor, "SELECT category_id FROM categories WHERE category_name = ?", (name,))
    return cursor.fetchone()[0]


def upsert_venue(cursor, name, address_line, city, postcode, map_url):
    execute(
        cursor,
        "SELECT venue_id FROM venues WHERE venue_name = ? AND postcode = ?",
        (name, postcode),
    )
    row = cursor.fetchone()
    if row:
        execute(
            cursor,
            """
            UPDATE venues
            SET address_line = ?, city = ?, map_url = ?
            WHERE venue_id = ?
            """,
            (address_line, city, map_url, row[0]),
        )
        return row[0]

    execute(
        cursor,
        """
        INSERT INTO venues (venue_name, address_line, city, postcode, map_url)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, address_line, city, postcode, map_url),
    )
    execute(
        cursor,
        "SELECT venue_id FROM venues WHERE venue_name = ? AND postcode = ?",
        (name, postcode),
    )
    return cursor.fetchone()[0]


def upsert_event(cursor, event, category_id, venue_id):
    execute(cursor, "SELECT event_id FROM events WHERE event_title = ?", (event["event_title"],))
    row = cursor.fetchone()
    values = (
        category_id,
        venue_id,
        event["event_description"],
        event["event_date"],
        event["start_time"],
        event["price_label"],
        event["image_url"],
    )

    if row:
        execute(
            cursor,
            """
            UPDATE events
            SET category_id = ?, venue_id = ?, event_description = ?, event_date = ?,
                start_time = ?, price_label = ?, image_url = ?
            WHERE event_id = ?
            """,
            values + (row[0],),
        )
        return

    execute(
        cursor,
        """
        INSERT INTO events
        (category_id, venue_id, event_title, event_description, event_date, start_time,
         price_label, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (category_id, venue_id, event["event_title"]) + values[2:],
    )


def find_event_id(cursor, event_name):
    execute(
        cursor,
        "SELECT event_id FROM events WHERE LOWER(event_title) = LOWER(?)",
        (event_name,),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def is_valid_email(email):
    return bool(EMAIL_PATTERN.fullmatch(email))


def is_strong_password(password):
    return (
        len(password) >= 8
        and any(character.isalpha() for character in password)
        and any(character.isdigit() for character in password)
    )


def is_unique_constraint_error(exc):
    if isinstance(exc, sqlite3.IntegrityError):
        return True

    try:
        import mysql.connector
    except ImportError:
        return False

    return isinstance(exc, mysql.connector.IntegrityError)


def make_booking_reference():
    timestamp = datetime.now(timezone.utc).strftime("%y%m%d%H%M%S")
    return f"BB{timestamp}{secrets.token_hex(3).upper()}"


def local_next_url(value):
    if not value or value.startswith(("http://", "https://", "//")):
        return "events.html"
    return value


for route, template_name in PAGES.items():
    app.add_url_rule(
        route,
        endpoint=f"page_{route.strip('/').replace('-', '_').replace('.', '_') or 'home'}",
        view_func=lambda template_name=template_name: render_template(template_name),
    )


@app.get("/dist/<path:filename>")
def dist_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, "dist"), filename)


@app.get("/assets/<path:filename>")
def asset_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, "assets"), filename)


@app.post("/api/create-account")
def create_account():
    payload = request.get_json(silent=True) or request.form
    email = (payload.get("email") or "").strip().lower()
    confirm_email = (payload.get("confirmEmail") or "").strip().lower()
    password = payload.get("password") or ""
    confirm_password = payload.get("confirmPassword") or ""

    if not is_valid_email(email):
        return jsonify({"ok": False, "message": "Please enter a valid email address."}), 400
    if email != confirm_email:
        return jsonify({"ok": False, "message": "The email addresses do not match."}), 400
    if not is_strong_password(password):
        return jsonify({"ok": False, "message": "Password must be at least 8 characters and include a letter and a number."}), 400
    if password != confirm_password:
        return jsonify({"ok": False, "message": "The passwords do not match."}), 400

    try:
        with closing(get_db_connection()) as conn:
            cursor = conn.cursor()
            execute(
                cursor,
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, generate_password_hash(password)),
            )
            conn.commit()
    except Exception as exc:
        if is_unique_constraint_error(exc):
            return jsonify({"ok": False, "message": "This email is already registered."}), 409
        return jsonify({"ok": False, "message": "Database error. Please try again."}), 500

    return jsonify(
        {
            "ok": True,
            "email": email,
            "message": "Account created. Please sign in to continue.",
            "savedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    )


@app.post("/api/sign-in")
def sign_in():
    payload = request.get_json(silent=True) or request.form
    email = (payload.get("email") or payload.get("siEmail") or "").strip().lower()
    password = payload.get("password") or payload.get("siPassword") or ""
    next_url = local_next_url(payload.get("next") or "events.html")

    if not email or not password:
        return jsonify({"ok": False, "message": "Please enter your email and password."}), 400

    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        execute(
            cursor,
            "SELECT user_id, email, password_hash FROM users WHERE LOWER(email) = LOWER(?)",
            (email,),
        )
        user = cursor.fetchone()

    if not user or not check_password_hash(user[2], password):
        return jsonify({"ok": False, "message": "Email or password is incorrect."}), 401

    session["user_id"] = user[0]
    session["email"] = user[1]
    return jsonify({"ok": True, "message": "Signed in successfully.", "redirectTo": next_url})


@app.get("/api/session")
def session_status():
    return jsonify({"loggedIn": bool(session.get("user_id")), "email": session.get("email")})


@app.post("/api/sign-out")
def sign_out():
    session.clear()
    return jsonify({"ok": True})


@app.post("/api/book-ticket")
def book_ticket():
    if not session.get("user_id"):
        return jsonify({"ok": False, "message": "Please sign in before booking."}), 401

    payload = request.get_json(silent=True) or request.form
    event_name = (payload.get("eventName") or "").strip()
    attendee_name = (payload.get("attendeeName") or "").strip()
    attendee_email = (payload.get("attendeeEmail") or "").strip().lower()
    attendee_phone = (payload.get("attendeePhone") or "").strip()
    special_requests = (payload.get("specialRequests") or "").strip()
    card_name = (payload.get("cardName") or "").strip()
    card_number = (payload.get("cardNumber") or "").strip()
    expiry = (payload.get("expiry") or "").strip()
    cvv = (payload.get("cvv") or "").strip()

    try:
        ticket_quantity = max(1, min(MAX_TICKETS_PER_BOOKING, int(payload.get("ticketQuantity") or 1)))
    except ValueError:
        ticket_quantity = 1

    if not event_name:
        return jsonify({"ok": False, "message": "Choose an event before booking."}), 400
    if not attendee_name or not attendee_email:
        return jsonify({"ok": False, "message": "Please enter the ticket holder name and email."}), 400
    if not is_valid_email(attendee_email):
        return jsonify({"ok": False, "message": "Please enter a valid ticket holder email."}), 400
    if not card_name or not card_number or not expiry or not cvv:
        return jsonify({"ok": False, "message": "Please enter the payment details."}), 400

    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        event_id = find_event_id(cursor, event_name)
        if not event_id:
            return jsonify({"ok": False, "message": "This event was not found."}), 404

        reference = make_booking_reference()
        execute(
            cursor,
            """
            INSERT INTO bookings
            (user_id, event_id, attendee_name, attendee_email, attendee_phone,
             ticket_quantity, special_requests, booking_status, payment_status,
             payment_reference)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'confirmed', 'accepted', ?)
            """,
            (
                session["user_id"],
                event_id,
                attendee_name,
                attendee_email,
                attendee_phone,
                ticket_quantity,
                special_requests,
                reference,
            ),
        )
        conn.commit()

    return jsonify(
        {
            "ok": True,
            "message": "Payment accepted. Check your email for the ticket.",
            "reference": reference,
            "ticketNumber": reference,
            "email": attendee_email,
            "eventName": event_name,
            "ticketQuantity": ticket_quantity,
        }
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=os.getenv("FLASK_DEBUG", "").lower() == "true")
