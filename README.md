# MedMate: Medicine Reminder and Expiry Tracker

MedMate helps people remember their medicines. Users add medicines and schedules, get reminders,
and mark each dose as taken or skipped. A linked caregiver is alerted when a dose is missed.

> MedMate is a reminder tool. It does not give medical advice, recommend doses or check drug interactions.

## Features
- Register and log in (bcrypt password hashing, JWT tokens)
- Add, edit and delete medicines; each user only sees their own data
- Schedules that create one dose per day; times stored in UTC and shown in the user's time zone
- Background scheduler (APScheduler) for reminders and caregiver alerts after a missed dose
- Expiry and low-stock alerts, and a weekly adherence report
- Simple web interface

## Tech stack
Python, FastAPI, SQLAlchemy, SQLite (PostgreSQL ready), JWT, bcrypt, APScheduler, HTML/CSS/JavaScript, pytest

## Run locally
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload

Open http://127.0.0.1:8000 for the app and http://127.0.0.1:8000/docs for the API.

## Tests
    python -m pytest

## Notes
Reminders print to the console. Telegram sending is built in and activates when TELEGRAM_BOT_TOKEN is set in .env.

## Possible improvements
Alembic migrations, Celery for multi-instance scheduling, email reminders, Docker and cloud deployment.