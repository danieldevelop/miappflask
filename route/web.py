"""
=====================================
Author: Daniel Gómez
Date: 2024-06-01
Contacto: daniel.gomezgo93@gmail.com
--
Version Python => 3.11.9
=====================================

Rutas a paginas del aplicativo hacia archivos HTML (Renderizados).
"""

from flask import Blueprint, render_template, request

""" Se crea un Blueprint en lugar de una nueva instancia de Flask para organizar mejor el código. """
web = Blueprint('web', __name__)

""" Cualquiera de estas 3 rutas puede ser usada para acceder a la página de inicio. """
@web.route('/')
@web.route('/index')
@web.route('/home')
def index():
    return render_template('index.html')

@web.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usu = request.form.get('username'  '').strip()
        passw = request.form.get('password', '')
        remember = request.form.get('remember_me') == 'true'

        # Solo para verificar que llega los datos
        print(f"Usuario: {usu}\nPassword: {passw}\nRemember: {remember}")

    return render_template('pages/login.html')

