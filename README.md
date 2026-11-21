# MedMate: Medicine Reminder and Expiry Tracker

MedMate helps people remember their medicines. Users add medicines and schedules, get reminders on Telegram,
and mark each dose as taken or skipped. A linked caregiver is alerted when a dose is missed.

> MedMate is a reminder tool. It does not give medical advice, recommend doses or check drug interactions.

## Features
- Register and log in (bcrypt password hashing, JWT tokens)
- Add, edit and delete medicines; each user only sees their own data
- Schedules that create one dose per day; times stored in UTC and shown in the user's time zone
- Duplicate and overlapping schedules are rejected
- Background scheduler (APScheduler): each reminder is sent once, and a caregiver is alerted if a dose is missed for 30 minutes
- Reminders sent through the Telegram Bot API
- Expiry and low-stock alerts, and a weekly adherence report
- Simple web interface (HTML, CSS, JavaScript)

## Tech stack
Python, FastAPI, SQLAlchemy, PostgreSQL (SQLite for local testing), JWT, bcrypt, APScheduler, Telegram Bot API, HTML/CSS/JavaScript, pytest

## Run locally
1. Create and activate a virtual environment, then install the libraries:

        python -m venv venv
        venv\Scripts\activate
        pip install -r requirements.txt

2. Create a `.env` file in the project folder:

        SECRET_KEY=a-long-random-string-of-32-or-more-characters
        TELEGRAM_BOT_TOKEN=your-bot-token        # optional
        DATABASE_URL=postgresql://...            # optional, uses SQLite if not set

3. Start the server:

        uvicorn app.main:app --reload

Open http://127.0.0.1:8000 for the app and http://127.0.0.1:8000/docs for the API.

## Telegram reminders (optional)
1. Create a bot with @BotFather and put its token in `.env` as `TELEGRAM_BOT_TOKEN`.
2. Send any message to your bot, then open `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your chat ID.
3. Save the chat ID under Settings in the app.

Without a token, reminders are printed in the server console instead.

## Tests

    python -m pytest

The tests use a temporary SQLite database and do not touch your real data.

## Project structure
- `app/` : API routes, models, authentication, scheduler and notifications
- `static/index.html` : the web interface
- `tests/` : pytest tests

## Possible improvements
Alembic migrations, Celery for multi-instance scheduling, email reminders, Docker and cloud deployment.