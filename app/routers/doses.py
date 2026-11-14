from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db, utcnow
from ..models import Caregiver, DoseLog, Medicine, Schedule, User
from ..schemas import CaregiverIn, DoseUpdate

router = APIRouter(tags=["doses"])


def user_doses(db: Session, user: User):
    """Doses that belong to this user (dose -> schedule -> medicine -> user)."""
    return (
        db.query(DoseLog, Medicine)
        .join(Schedule, DoseLog.schedule_id == Schedule.id)
        .join(Medicine, Schedule.medicine_id == Medicine.id)
        .filter(Medicine.user_id == user.id)
    )


def dose_json(dose: DoseLog, med: Medicine, tz: ZoneInfo):
    local = dose.due_at.replace(tzinfo=timezone.utc).astimezone(tz)
    return {"id": dose.id, "medicine": med.name, "dosage": med.dosage,
            "due_local": local.strftime("%H:%M"), "status": dose.status}


@router.get("/doses/today")
def doses_today(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    tz = ZoneInfo(user.timezone)
    today = datetime.now(tz).date()
    start = datetime.combine(today, time.min, tzinfo=tz).astimezone(timezone.utc).replace(tzinfo=None)
    rows = (user_doses(db, user)
            .filter(DoseLog.due_at >= start, DoseLog.due_at < start + timedelta(days=1))
            .order_by(DoseLog.due_at).all())
    return [dose_json(d, m, tz) for d, m in rows]


@router.patch("/doses/{dose_id}")
def update_dose(dose_id: int, data: DoseUpdate, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    row = user_doses(db, user).filter(DoseLog.id == dose_id).first()
    if not row:
        raise HTTPException(404, "Dose not found")
    dose, med = row
    if data.status == "taken" and dose.status != "taken":
        med.quantity_left = max(0, med.quantity_left - 1)
    dose.status = data.status
    db.commit()
    return dose_json(dose, med, ZoneInfo(user.timezone))


@router.get("/alerts")
def alerts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    soon = date.today() + timedelta(days=30)
    meds = db.query(Medicine).filter(Medicine.user_id == user.id).all()
    return {
        "expiring": [{"id": m.id, "name": m.name, "expiry_date": m.expiry_date.isoformat()}
                     for m in meds if m.expiry_date <= soon],
        "low_stock": [{"id": m.id, "name": m.name, "quantity_left": m.quantity_left}
                      for m in meds if m.quantity_left <= 5],
    }


@router.get("/report/weekly")
def weekly_report(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    now = utcnow()
    rows = user_doses(db, user).filter(DoseLog.due_at >= now - timedelta(days=7), DoseLog.due_at <= now).all()
    total = len(rows)
    taken = sum(1 for d, _ in rows if d.status == "taken")
    skipped = sum(1 for d, _ in rows if d.status == "skipped")
    return {"total": total, "taken": taken, "skipped": skipped,
            "missed": total - taken - skipped,
            "adherence_percent": round(100 * taken / total) if total else None}


@router.post("/caregivers", status_code=201)
def add_caregiver(data: CaregiverIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cg = db.query(User).filter(User.email == data.email.lower()).first()
    if not cg:
        raise HTTPException(404, "No user with that email. Ask them to register first.")
    if cg.id == user.id:
        raise HTTPException(400, "You cannot be your own caregiver")
    exists = db.query(Caregiver).filter(Caregiver.patient_id == user.id, Caregiver.caregiver_id == cg.id).first()
    if not exists:
        db.add(Caregiver(patient_id=user.id, caregiver_id=cg.id))
        db.commit()
    return {"caregiver": cg.name}


@router.get("/caregivers")
def list_caregivers(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = (db.query(User).join(Caregiver, Caregiver.caregiver_id == User.id)
            .filter(Caregiver.patient_id == user.id).all())
    return [{"name": u.name, "email": u.email} for u in rows]