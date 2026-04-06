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

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from models.user import User
from utils.auth import login_required

""" Se crea un Blueprint en lugar de una nueva instancia de Flask para organizar mejor el código. """
web = Blueprint('web', __name__)

@web.route('/')
def index():
    return render_template('index.html')

@web.route('/login', methods=['GET', 'POST'])
def login():
    if session.get("user_id"):
        return redirect(url_for("web.dashboard"))

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""
        remember = bool(data.get("remember_me", False))

        if not username or not password:
            return jsonify({"ok": False, "message": "Credenciales invalidas"}), 400

        user = User.query.filter_by(username=username, is_active=True).first()

        if not user or not user.check_password(password):
            return jsonify({"ok": False, "message": "Credenciales invalidas"}), 401

        session["user_id"] = user.id
        session["username"] = user.username
        session.permanent = remember

        return jsonify({"ok": True, "message": "Login correcto", "redirect": "/dashboard"}), 200

    return render_template("pages/login.html")

@web.route("/dashboard")
@login_required
def dashboard():
    return render_template("pages/dashboard.html")

@web.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return jsonify({"ok": True, "message": "Sesion cerrada", "redirect": "/login"}), 200

