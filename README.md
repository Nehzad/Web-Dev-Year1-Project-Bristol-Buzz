# Bristol Buzz Website

Bristol Buzz is a Flask-based events website for discovering Bristol events, creating an account, and booking demo tickets. It includes static HTML pages, shared styling/assets, and database-backed account and booking routes.

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

Create your local environment file:

```bash
copy .env.example .env
```

Update `.env` with your local MySQL password, then create the database:

```bash
mysql -u root -p < database_schema.sql
```

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
