"""
=====================================
Author: Daniel Gómez
Date: 2024-06-01
Contacto: daniel.gomezgo93@gmail.com
--
Version Python => 3.11.9
=====================================

Punto de partida de la aplicación.
"""

import os
from sqlalchemy import text
from flask import Flask
from dotenv import load_dotenv
from extensions import db

load_dotenv()  # Carga las variables de entorno desde el archivo .env

# Crear carpeta instance si no existe
base_dir = os.path.dirname(os.path.abspath(__file__))
instance_path = os.path.join(base_dir, "instance")
os.makedirs(instance_path, exist_ok=True)


def build_database_uri() -> str:
    """Normaliza DATABASE_URL para que SQLite siempre apunte a una ruta valida."""
    raw_uri = os.getenv("DATABASE_URL", "").strip()

    if not raw_uri:
        db_path = os.path.join(instance_path, "miapp.db")
        return f"sqlite:///{db_path.replace(os.sep, '/')}"

    if raw_uri.startswith("sqlite:///"):
        sqlite_target = raw_uri[len("sqlite:///"):]

        # Evita duplicar "instance/" cuando Flask-SQLAlchemy ya usa esa carpeta base.
        if sqlite_target.startswith("instance/") or sqlite_target.startswith("instance\\"):
            sqlite_target = sqlite_target.split("instance", 1)[1].lstrip("/\\")

        if sqlite_target in ("", ":memory:"):
            return raw_uri

        if not os.path.isabs(sqlite_target):
            sqlite_target = os.path.join(instance_path, sqlite_target)

        os.makedirs(os.path.dirname(sqlite_target), exist_ok=True)
        return f"sqlite:///{sqlite_target.replace(os.sep, '/')}"

    return raw_uri


def run_sqlite_compat_migrations() -> None:
    """Aplica ajustes minimos de esquema en SQLite para bases existentes."""
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if not db_uri.startswith("sqlite:///"):
        return

    with db.engine.connect() as conn:
        columns = conn.execute(text("PRAGMA table_info(users)")).fetchall()
        existing = {row[1] for row in columns}
        if "webauthn_enabled" not in existing:
            conn.execute(
                text(
                    "ALTER TABLE users ADD COLUMN webauthn_enabled BOOLEAN NOT NULL DEFAULT 0"
                )
            )
            conn.commit()

""" Se crea intancia de Flask para iniciar un servidor web. """
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-key")
app.config["SQLALCHEMY_DATABASE_URI"] = build_database_uri()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

""" Importamos y registramos el Blueprint """
from route.web import web
app.register_blueprint(web)

# Importa modelos para que SQLAlchemy los registre
from models.user import User  # noqa: F401
from models.webauthn_credential import WebauthnCredential  # noqa: F401

with app.app_context():
    db.create_all()
    run_sqlite_compat_migrations()

if (__name__ == "__main__"):
    os.system("cls" if os.name == "nt" else "clear")
    print("Se ha iniciado la aplicación en el puerto 8000")
    app.run(debug=True, port=8000)