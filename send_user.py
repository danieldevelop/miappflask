from app import app
from extensions import db
from models.user import User

with app.app_context():
    exists = User.query.filter_by(username="daniel").first()
    if exists:
        print("El usuario 'daniel' ya existe.")
    else:
        u = User(username="daniel")
        u.set_password("Pass1234")
        db.session.add(u)
        db.session.commit()
        print("Usuario creado correctamente.")
