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

""" Se crea intancia de Flask para iniciar un servidor web. """
app = Flask(__name__)

""" Importamos y registramos el Blueprint """
from route.web import web
app.register_blueprint(web)

if (__name__ == "__main__"):
    os.system("cls" if os.name == "nt" else "clear")
    print("Se ha iniciado la aplicación en el puerto 8000")
    app.run(debug=True, port=8000)