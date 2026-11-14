from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..auth import create_token, get_current_user, hash_password, verify_password
from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserUpdate

router = APIRouter(prefix="/auth", tags=["auth"])


def check_tz(name: str):
    try:
        ZoneInfo(name)
    except Exception:
        raise HTTPException(400, f"Unknown timezone: {name}")


def user_json(u: User):
    return {"id": u.id, "name": u.name, "email": u.email,
            "timezone": u.timezone, "telegram_chat_id": u.telegram_chat_id}


@router.post("/register", status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    check_tz(data.timezone)
    email = data.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "Email already registered")
    user = User(name=data.name, email=email, password_hash=hash_password(data.password),
                timezone=data.timezone, telegram_chat_id=data.telegram_chat_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_json(user)


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username.lower()).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Wrong email or password")
    return {"access_token": create_token(user.id), "token_type": "bearer"}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return user_json(user)


@router.put("/me")
def update_me(data: UserUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if data.timezone:
        check_tz(data.timezone)
        user.timezone = data.timezone
    if data.telegram_chat_id is not None:
        user.telegram_chat_id = data.telegram_chat_id or None
    db.commit()
    return user_json(user)