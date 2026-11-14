from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db, utcnow
from ..models import DoseLog, Medicine, Schedule, User
from ..schemas import MedicineIn, ScheduleIn

router = APIRouter(prefix="/medicines", tags=["medicines"])


def get_owned(db: Session, user: User, med_id: int) -> Medicine:
    """Return the medicine only if it belongs to this user, otherwise 404."""
    med = db.query(Medicine).filter(Medicine.id == med_id, Medicine.user_id == user.id).first()
    if not med:
        raise HTTPException(404, "Medicine not found")
    return med


def med_json(m: Medicine):
    return {"id": m.id, "name": m.name, "dosage": m.dosage,
            "expiry_date": m.expiry_date.isoformat(), "quantity_left": m.quantity_left}


@router.post("", status_code=201)
def add_medicine(data: MedicineIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    med = Medicine(**data.model_dump(), user_id=user.id)
    db.add(med)
    db.commit()
    db.refresh(med)
    return med_json(med)


@router.get("")
def list_medicines(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    meds = db.query(Medicine).filter(Medicine.user_id == user.id).order_by(Medicine.name).all()
    return [med_json(m) for m in meds]


@router.put("/{med_id}")
def update_medicine(med_id: int, data: MedicineIn, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    med = get_owned(db, user, med_id)
    for key, value in data.model_dump().items():
        setattr(med, key, value)
    db.commit()
    return med_json(med)


@router.delete("/{med_id}", status_code=204)
def delete_medicine(med_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    med = get_owned(db, user, med_id)
    # Delete the children first: doses, then schedules, then the medicine itself.
    sched_ids = [s.id for s in db.query(Schedule).filter(Schedule.medicine_id == med.id)]
    if sched_ids:
        db.query(DoseLog).filter(DoseLog.schedule_id.in_(sched_ids)).delete(synchronize_session=False)
        db.query(Schedule).filter(Schedule.id.in_(sched_ids)).delete(synchronize_session=False)
    db.delete(med)
    db.commit()
    return Response(status_code=204)


@router.post("/{med_id}/schedules", status_code=201)
def add_schedule(med_id: int, data: ScheduleIn, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    med = get_owned(db, user, med_id)
    if data.end_date < data.start_date:
        raise HTTPException(400, "End date must be on or after start date")
    if (data.end_date - data.start_date).days > 366:
        raise HTTPException(400, "A schedule can cover at most one year")

    sched = Schedule(medicine_id=med.id, time_of_day=data.time_of_day,
                     start_date=data.start_date, end_date=data.end_date)
    db.add(sched)
    db.flush()  # gives sched an id without finishing the transaction

    # Create one dose per day. Local time -> UTC. Doses already in the past are skipped.
    tz = ZoneInfo(user.timezone)
    now, day, created = utcnow(), data.start_date, 0
    while day <= data.end_date:
        due_local = datetime.combine(day, data.time_of_day, tzinfo=tz)
        due_utc = due_local.astimezone(timezone.utc).replace(tzinfo=None)
        if due_utc >= now:
            db.add(DoseLog(schedule_id=sched.id, due_at=due_utc))
            created += 1
        day += timedelta(days=1)
    db.commit()
    return {"schedule_id": sched.id, "doses_created": created}


@router.get("/{med_id}/schedules")
def list_schedules(med_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    med = get_owned(db, user, med_id)
    rows = db.query(Schedule).filter(Schedule.medicine_id == med.id).all()
    return [{"id": s.id, "time_of_day": s.time_of_day.strftime("%H:%M"),
             "start_date": s.start_date.isoformat(), "end_date": s.end_date.isoformat()} for s in rows]