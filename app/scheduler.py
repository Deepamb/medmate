from datetime import timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from .database import SessionLocal, utcnow
from .models import Caregiver, DoseLog, Medicine, Schedule, User
from .notify import send_telegram


def _pending_rows(db):
    return (
        db.query(DoseLog, Medicine, User)
        .join(Schedule, DoseLog.schedule_id == Schedule.id)
        .join(Medicine, Schedule.medicine_id == Medicine.id)
        .join(User, Medicine.user_id == User.id)
        .filter(DoseLog.status == "pending")
    )


def check_reminders():
    """Every minute: remind users about doses that are due and not yet reminded."""
    db = SessionLocal()
    try:
        now = utcnow()
        rows = _pending_rows(db).filter(
            DoseLog.reminder_sent == False,  # noqa: E712
            DoseLog.due_at <= now,
            DoseLog.due_at >= now - timedelta(hours=6),
        ).all()
        for dose, med, user in rows:
            send_telegram(user.telegram_chat_id, f"Time to take {med.name} ({med.dosage}).")
            dose.reminder_sent = True
        db.commit()
    finally:
        db.close()


def check_missed_doses():
    """Every minute: alert caregivers when a dose is 30+ minutes overdue."""
    db = SessionLocal()
    try:
        cutoff = utcnow() - timedelta(minutes=30)
        rows = _pending_rows(db).filter(
            DoseLog.caregiver_alerted == False,  # noqa: E712
            DoseLog.due_at <= cutoff,
            DoseLog.due_at >= cutoff - timedelta(hours=6),
        ).all()
        for dose, med, patient in rows:
            caregivers = (
                db.query(User)
                .join(Caregiver, Caregiver.caregiver_id == User.id)
                .filter(Caregiver.patient_id == patient.id)
                .all()
            )
            for cg in caregivers:
                send_telegram(cg.telegram_chat_id, f"{patient.name} has not taken {med.name} ({med.dosage}) yet.")
            dose.caregiver_alerted = True
        db.commit()
    finally:
        db.close()


scheduler = BackgroundScheduler()
scheduler.add_job(check_reminders, "interval", minutes=1, id="reminders")
scheduler.add_job(check_missed_doses, "interval", minutes=1, id="missed")