# MySQL Verification

Verified on April 24, 2026 using MySQL Community Server 8.0.

The `database_schema.sql` script was run successfully and created the `bristol_buzz` database with these tables:

- `bookings`
- `categories`
- `events`
- `users`
- `venues`

Seed data check:

- `events` contains 7 case-study events.
- Event dates are future-facing from the submission date and use local image paths from `assets/events`.

Flask integration check:

- The `/api/create-account` endpoint was tested using the MySQL backend.
- A test account was created successfully.
- The `/api/sign-in` endpoint created a working Flask session for the test account.
- The `/api/book-ticket` endpoint stored a `Great Bristol Half Marathon` booking with status `confirmed` and payment status `accepted`.
- The temporary test account was deleted after verification, leaving the database clean for submission.
