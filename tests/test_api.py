import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["DISABLE_SCHEDULER"] = "1"

from datetime import date, timedelta  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

PASSWORD = "password123"


def signup(c, email, name="Test"):
    r = c.post("/auth/register", json={"name": name, "email": email, "password": PASSWORD, "timezone": "UTC"})
    assert r.status_code == 201, r.text
    r = c.post("/auth/login", data={"username": email, "password": PASSWORD})
    assert r.status_code == 200
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def med(name="Paracetamol", qty=10):
    return {"name": name, "dosage": "500mg", "expiry_date": str(date.today() + timedelta(days=200)), "quantity_left": qty}


def test_register_login_and_wrong_password():
    with TestClient(app) as c:
        h = signup(c, "a@example.com")
        assert c.get("/auth/me", headers=h).json()["email"] == "a@example.com"
        assert c.post("/auth/login", data={"username": "a@example.com", "password": "nope-nope"}).status_code == 401
        assert c.get("/medicines").status_code == 401


def test_users_cannot_see_each_others_medicines():
    with TestClient(app) as c:
        a, b = signup(c, "own1@example.com"), signup(c, "own2@example.com")
        mid = c.post("/medicines", json=med(), headers=a).json()["id"]
        assert c.get("/medicines", headers=b).json() == []
        assert c.put(f"/medicines/{mid}", json=med(), headers=b).status_code == 404
        assert c.delete(f"/medicines/{mid}", headers=b).status_code == 404
        assert len(c.get("/medicines", headers=a).json()) == 1


def test_schedule_and_mark_dose_taken():
    with TestClient(app) as c:
        h = signup(c, "dose@example.com")
        mid = c.post("/medicines", json=med(qty=3), headers=h).json()["id"]
        r = c.post(f"/medicines/{mid}/schedules", headers=h,
                   json={"time_of_day": "23:59:00", "start_date": str(date.today()), "end_date": str(date.today())})
        assert r.status_code == 201
        today = c.get("/doses/today", headers=h).json()
        assert len(today) == 1 and today[0]["status"] == "pending"
        assert c.patch(f"/doses/{today[0]['id']}", json={"status": "taken"}, headers=h).json()["status"] == "taken"
        assert c.get("/medicines", headers=h).json()[0]["quantity_left"] == 2