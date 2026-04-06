"""Prueba rapida de Fase 2/2.1 usando Flask test_client."""

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app, db
from models.user import User


def ensure_user() -> User:
    user = User.query.filter_by(username="smoke_user").first()
    if not user:
        user = User(username="smoke_user")
        user.set_password("Pass1234")
        db.session.add(user)
        db.session.commit()
    return user


def run() -> None:
    with app.app_context():
        user = ensure_user()
        user_id = user.id
        username = user.username

    client = app.test_client()

    login_bad = client.post("/login", json={"username": username, "password": "bad"})
    print("/login bad =>", login_bad.status_code, login_bad.is_json)

    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["username"] = username

    toggle_resp = client.post("/webauthn/login-toggle", json={"enabled": False})
    print("/webauthn/login-toggle =>", toggle_resp.status_code, toggle_resp.is_json)

    recent_resp = client.get("/auth-events/recent?limit=5")
    print("/auth-events/recent =>", recent_resp.status_code, recent_resp.is_json)


if __name__ == "__main__":
    run()

