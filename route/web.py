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
from extensions import db
from models.user import User
from utils.auth import api_login_required, page_login_required
import io
import base64
import pyotp
import qrcode

def build_qr_base64(content: str) -> str:
    img = qrcode.make(content)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


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

        # Si tiene TOTP activado, aun no se crea la sesion final
        if user.two_factor_enabled and user.two_factor_method == "totp" and user.totp_secret:
            session["pre_2fa_user_id"] = user.id
            session["pre_2fa_username"] = user.username
            session["pre_2fa_remember"] = remember

            return jsonify({
                "ok": True,
                "requires_2fa": True,
                "method": "totp",
                "redirect": url_for("web.verify_2fa")
            }), 200

        # Login normal si no tiene 2FA
        session["user_id"] = user.id
        session["username"] = user.username
        session.permanent = remember

        return jsonify({
            "ok": True,
            "message": "Login correcto",
            "redirect": url_for("web.dashboard")
        }), 200

    return render_template("pages/login.html")

@web.route("/2fa/setup", methods=["GET"])
@page_login_required
def setup_2fa():
    user = db.session.get(User, session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("web.login"))

    if user.two_factor_enabled and user.totp_secret:
        return redirect(url_for("web.dashboard"))

    secret = session.get("pending_totp_secret")
    if not secret:
        secret = pyotp.random_base32()
        session["pending_totp_secret"] = secret

    provisioning_uri = pyotp.TOTP(secret).provisioning_uri(
        name=user.username,
        issuer_name="MiAppFlask"
    )

    qr_code_b64 = build_qr_base64(provisioning_uri)

    return render_template(
        "pages/totp_setup.html",
        qr_code_b64=qr_code_b64,
        secret=secret
    )

@web.route("/2fa/enable", methods=["POST"])
@api_login_required
def enable_2fa():
    user = db.session.get(User, session["user_id"])
    if not user:
        session.clear()
        return jsonify({"ok": False, "message": "Sesion invalida"}), 401

    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()
    secret = session.get("pending_totp_secret")

    if not secret:
        return jsonify({"ok": False, "message": "No hay configuracion TOTP pendiente"}), 400

    if not code:
        return jsonify({"ok": False, "message": "Codigo requerido"}), 400

    totp = pyotp.TOTP(secret)

    if not totp.verify(code, valid_window=1):
        return jsonify({"ok": False, "message": "Codigo TOTP invalido"}), 400

    user.totp_secret = secret
    user.two_factor_enabled = True
    user.two_factor_method = "totp"

    db.session.commit()

    session.pop("pending_totp_secret", None)

    return jsonify({
        "ok": True,
        "message": "2FA activado correctamente",
        "redirect": url_for("web.dashboard")
    }), 200

@web.route("/verify-2fa", methods=["GET", "POST"])
def verify_2fa():
    if session.get("user_id"):
        return redirect(url_for("web.dashboard"))

    pending_user_id = session.get("pre_2fa_user_id")
    if not pending_user_id:
        return redirect(url_for("web.login"))

    user = db.session.get(User, pending_user_id)
    if not user or not user.two_factor_enabled or not user.totp_secret:
        session.pop("pre_2fa_user_id", None)
        session.pop("pre_2fa_username", None)
        session.pop("pre_2fa_remember", None)
        return redirect(url_for("web.login"))

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        code = (data.get("code") or "").strip()

        if not code:
            return jsonify({"ok": False, "message": "Codigo requerido"}), 400

        totp = pyotp.TOTP(user.totp_secret)

        if not totp.verify(code, valid_window=1):
            return jsonify({"ok": False, "message": "Codigo invalido"}), 401

        remember = bool(session.get("pre_2fa_remember", False))

        session.pop("pre_2fa_user_id", None)
        session.pop("pre_2fa_username", None)
        session.pop("pre_2fa_remember", None)

        session["user_id"] = user.id
        session["username"] = user.username
        session.permanent = remember

        return jsonify({
            "ok": True,
            "message": "Segundo factor validado correctamente",
            "redirect": url_for("web.dashboard")
        }), 200

    return render_template("pages/verify_2fa.html")

@web.route("/dashboard")
@page_login_required
def dashboard():
    return render_template("pages/dashboard.html")

@web.route("/logout", methods=["POST"])
@api_login_required
def logout():
    session.clear()
    return jsonify({"ok": True, "message": "Sesion cerrada", "redirect": "/login"}), 200

