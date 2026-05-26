# Bristol Buzz Website

Bristol Buzz is a first-year Flask web development project for discovering Bristol events, creating an account, and booking demo tickets. It includes static HTML pages, shared styling/assets, and database-backed account and booking routes.

## Project Contents

- `BristolBuzz.html` - home page
- `events.html` - event listings
- `account.html` - account creation and sign in
- `ticket.html` - demo ticket booking flow
- `curator.html` - curator page
- `app.py` - Flask app and API routes
- `database_schema.sql` - MySQL database schema
- `assets/` - event images
- `dist/` - generated/shared frontend assets

## Run Locally

Install the Python packages:

```bash
py -m pip install -r requirements.txt
```

Create your local environment file if you want to use MySQL:

```bash
copy .env.example .env
```

Update `.env` with your local MySQL password, then create the database:

```bash
mysql -u root -p < database_schema.sql
```

If `.env` is not configured for MySQL, the app falls back to a local SQLite database named `bristol_buzz.db`.

Run the website:

```bash
py run_server.py
```

Open:

```text
http://127.0.0.1:5000/
```

## Notes

Local database files, logs, cache files, and `.env` are intentionally excluded from GitHub.

The app expects `FLASK_SECRET_KEY` in `.env` for a persistent session key. If it is missing in development, Flask uses a temporary generated key for the current run.

## API Routes

- `POST /api/create-account` - creates a user account with email and password validation
- `POST /api/sign-in` - signs a user in and starts a session
- `GET /api/session` - returns the current session status
- `POST /api/sign-out` - clears the current session
- `POST /api/book-ticket` - books demo tickets for a signed-in user

## Tests

Run the basic Flask API tests:

```bash
py -m unittest discover
```
