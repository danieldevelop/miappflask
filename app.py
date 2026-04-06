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
from flask import Flask
from dotenv import load_dotenv
from extensions import db

load_dotenv()  # Carga las variables de entorno desde el archivo .env

""" Se crea intancia de Flask para iniciar un servidor web. """
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///miapp.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

""" Importamos y registramos el Blueprint """
from route.web import web
app.register_blueprint(web)

# Importa modelos para que SQLAlchemy los registre
from models.user import User  # noqa: F401

with app.app_context():
    db.create_all()

if (__name__ == "__main__"):
    os.system("cls" if os.name == "nt" else "clear")
    print("Se ha iniciado la aplicación en el puerto 8000")
    app.run(debug=True, port=8000)