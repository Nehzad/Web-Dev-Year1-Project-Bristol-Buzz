# Bristol Buzz Week 2 and Week 3 Submission

## Week 2 Files

- `week2_database_design.md` contains the ERD, relationships, multiplicities, and two normalisation examples.
- `database_schema.sql` implements the ERD in MySQL.

To create the MySQL database:

```bash
mysql -u root -p < database_schema.sql
```

On this Windows laptop, MySQL is installed here, so this command also works:

```powershell
Get-Content database_schema.sql | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
```

## Week 3 Flask App

Install the Python packages:

```bash
py -m pip install -r requirements.txt
```

Run the Flask app:

```bash
py run_server.py
```

The app reads database settings from `.env`, so this project now uses the
local MySQL `bristol_buzz` database by default. To change the database later,
edit `.env` or set these variables in the terminal before running the server:

```bash
set DB_BACKEND=mysql
set MYSQL_HOST=localhost
set MYSQL_USER=root
set MYSQL_PASSWORD=your_password
set MYSQL_DATABASE=bristol_buzz
py run_server.py
```

Then open:

```text
http://127.0.0.1:5000/
```

The `account.html` create-account form sends data to `/api/create-account`. After the account is created, the page switches to sign-in and `/api/sign-in` creates a Flask session. Event booking opens `ticket.html`, which collects ticket holder details, accepts demo payment details, stores the booking in the `bookings` table through `/api/book-ticket`, and returns a payment accepted response. Demo card values are not stored.
