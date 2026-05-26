import os
import sqlite3
from contextlib import closing
from datetime import datetime

from flask import Flask, jsonify, render_template, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_PATH = os.path.join(BASE_DIR, "bristol_buzz.db")


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

app = Flask(__name__, template_folder=BASE_DIR)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "bristol-buzz-dev-session-key")


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
                CREATE TABLE IF NOT EXISTS events (
                    event_id INT AUTO_INCREMENT PRIMARY KEY,
                    event_title VARCHAR(160) NOT NULL UNIQUE
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
                    payment_reference VARCHAR(40),
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
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_title TEXT NOT NULL UNIQUE
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
                    payment_reference TEXT,
                    booked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (event_id) REFERENCES events(event_id)
                        ON DELETE RESTRICT
                )
                """
            )
            seed_events(cursor)

        ensure_booking_columns(cursor)
        conn.commit()


def ensure_booking_columns(cursor):
    if using_mysql():
        cursor.execute("SHOW COLUMNS FROM bookings")
        existing = {row[0] for row in cursor.fetchall()}
        columns = {
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
        columns = {
            "attendee_name": "TEXT NOT NULL DEFAULT ''",
            "attendee_email": "TEXT NOT NULL DEFAULT ''",
            "attendee_phone": "TEXT",
            "ticket_quantity": "INTEGER NOT NULL DEFAULT 1",
            "special_requests": "TEXT",
            "payment_status": "TEXT NOT NULL DEFAULT 'accepted'",
            "payment_reference": "TEXT",
        }

    for column, definition in columns.items():
        if column not in existing:
            cursor.execute(f"ALTER TABLE bookings ADD COLUMN {column} {definition}")


def seed_events(cursor):
    event_titles = [
        "International Balloon Fiesta",
        "Love Saves The Day",
        "Bristol Light Festival",
        "Opera: La Boheme",
        "Bristol Food Festival",
        "Bristol Comedy Festival",
        "Great Bristol Half Marathon",
    ]
    for title in event_titles:
        execute(cursor, "SELECT event_id FROM events WHERE event_title = ?", (title,))
        if cursor.fetchone() is None:
            execute(cursor, "INSERT INTO events (event_title) VALUES (?)", (title,))


def find_event_id(cursor, event_name):
    execute(
        cursor,
        "SELECT event_id FROM events WHERE LOWER(event_title) = LOWER(?)",
        (event_name,),
    )
    row = cursor.fetchone()
    return row[0] if row else None


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

    if not email or "@" not in email:
        return jsonify({"ok": False, "message": "Please enter a valid email address."}), 400
    if email != confirm_email:
        return jsonify({"ok": False, "message": "The email addresses do not match."}), 400
    if len(password) < 6:
        return jsonify({"ok": False, "message": "Password must be at least 6 characters."}), 400
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
        message = str(exc).lower()
        if "unique" in message or "duplicate" in message:
            return jsonify({"ok": False, "message": "This email is already registered."}), 409
        return jsonify({"ok": False, "message": "Database error. Please try again."}), 500

    return jsonify(
        {
            "ok": True,
            "email": email,
            "message": "Account created. Please sign in to continue.",
            "savedAt": datetime.utcnow().isoformat(timespec="seconds") + "Z",
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
        ticket_quantity = max(1, min(6, int(payload.get("ticketQuantity") or 1)))
    except ValueError:
        ticket_quantity = 1

    if not event_name:
        return jsonify({"ok": False, "message": "Choose an event before booking."}), 400
    if not attendee_name or not attendee_email:
        return jsonify({"ok": False, "message": "Please enter the ticket holder name and email."}), 400
    if not card_name or not card_number or not expiry or not cvv:
        return jsonify({"ok": False, "message": "Please enter the payment details."}), 400

    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        event_id = find_event_id(cursor, event_name)
        if not event_id:
            return jsonify({"ok": False, "message": "This event was not found."}), 404

        reference = "BB" + datetime.utcnow().strftime("%y%m%d%H%M%S")
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
    app.run(debug=True)
