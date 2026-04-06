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
from webauthn.helpers import options_to_json_dict
from models.user import User
from extensions import db
from models.webauthn_credential import WebauthnCredential
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
        if request.method == "POST":
            return jsonify({"ok": True, "message": "Sesion activa", "redirect": url_for("web.dashboard")}), 200
        return redirect(url_for("web.dashboard"))

    if request.method == "POST":
        try:
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
        except Exception:
            return jsonify({"ok": False, "message": "Error interno al iniciar sesion"}), 500

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
    user = db.session.get(User, session["user_id"])  # Obtener usuario
    if not user:
        session.clear()
        return redirect(url_for("web.login"))

    return render_template("pages/dashboard.html", user=user)  # Pasar usuario al template

@web.route("/logout", methods=["POST"])
@api_login_required
def logout():
    session.clear()
    return jsonify({"ok": True, "message": "Sesion cerrada", "redirect": "/login"}), 200


# ==================== WebAuthn/Passkeys ====================

@web.route("/webauthn/register-options", methods=["GET"])
@api_login_required
def webauthn_register_options():
    """Obtiene las opciones para registrar una credencial WebAuthn"""
    from utils.webauthn_utils import generate_registration_options

    user = db.session.get(User, session["user_id"])
    if not user:
        return jsonify({"ok": False, "message": "Sesión inválida"}), 401

    try:
        opts = generate_registration_options(user.username, str(user.id))
        options_json = options_to_json_dict(opts)

        # Guardar el challenge en la sesión
        session["webauthn_challenge"] = options_json["challenge"]
        session.modified = True

        return jsonify({
            "ok": True,
            "options": options_json
        }), 200
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400


@web.route("/webauthn/register-verify", methods=["POST"])
@api_login_required
def webauthn_register_verify():
    """Verifica y registra una credencial WebAuthn"""
    from utils.webauthn_utils import verify_registration
    from models.webauthn_credential import WebauthnCredential

    user = db.session.get(User, session["user_id"])
    if not user:
        return jsonify({"ok": False, "message": "Sesión inválida"}), 401

    data = request.get_json(silent=True) or {}
    credential_data = data.get("credential")
    device_name = (data.get("device_name") or "Mi dispositivo").strip()
    challenge = session.get("webauthn_challenge")

    if not credential_data or not challenge:
        return jsonify({"ok": False, "message": "Datos incompletos"}), 400

    try:
        verified, public_key, credential_id, sign_count = verify_registration(
            credential_data, challenge, str(user.id)
        )

        if not verified:
            return jsonify({"ok": False, "message": "Verificación fallida"}), 400

        # Verificar si ya existe esta credencial
        existing = WebauthnCredential.query.filter_by(
            credential_id=credential_id
        ).first()

        if existing:
            return jsonify({"ok": False, "message": "Esta credencial ya está registrada"}), 400

        # Guardar la credencial
        credential = WebauthnCredential(
            user_id=user.id,
            credential_id=credential_id,
            public_key=public_key,
            sign_count=sign_count,
            device_name=device_name,
        )

        db.session.add(credential)

        # Activar WebAuthn en el usuario
        user.webauthn_enabled = True

        db.session.commit()

        # Limpiar challenge de la sesión
        session.pop("webauthn_challenge", None)

        return jsonify({
            "ok": True,
            "message": "Credencial registrada correctamente",
            "credential": credential.to_dict()
        }), 200
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400


@web.route("/webauthn/authenticate-options", methods=["POST"])
def webauthn_authenticate_options():
    """Obtiene las opciones para autenticarse con WebAuthn"""
    from utils.webauthn_utils import generate_authentication_options

    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()

    if not username:
        return jsonify({"ok": False, "message": "Username requerido"}), 400

    try:
        # Verificar que el usuario existe y tiene WebAuthn habilitado
        user = User.query.filter_by(username=username, is_active=True).first()
        if not user or not user.webauthn_enabled:
            return jsonify({"ok": False, "message": "Usuario no tiene WebAuthn configurado"}), 400

        credentials = WebauthnCredential.query.filter_by(user_id=user.id).all()
        if not credentials:
            return jsonify({"ok": False, "message": "No hay credenciales WebAuthn registradas"}), 400

        credential_ids = [c.credential_id for c in credentials]
        opts = generate_authentication_options(credential_ids)
        options_json = options_to_json_dict(opts)

        # Guardar el challenge en la sesión
        session["webauthn_auth_challenge"] = options_json["challenge"]
        session["webauthn_auth_username"] = username
        session.modified = True

        return jsonify({
            "ok": True,
            "options": options_json
        }), 200
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400


@web.route("/webauthn/authenticate-verify", methods=["POST"])
def webauthn_authenticate_verify():
    """Verifica la autenticación con WebAuthn"""
    from utils.webauthn_utils import verify_authentication
    from datetime import datetime

    data = request.get_json(silent=True) or {}
    credential_data = data.get("credential")
    challenge = session.get("webauthn_auth_challenge")
    username = session.get("webauthn_auth_username")

    if not credential_data or not challenge or not username:
        return jsonify({"ok": False, "message": "Datos incompletos"}), 400

    try:
        user = User.query.filter_by(username=username, is_active=True).first()
        if not user:
            return jsonify({"ok": False, "message": "Usuario no encontrado"}), 401

        # Obtener la credencial
        credential_id = credential_data.get("id")
        credential = WebauthnCredential.query.filter_by(
            user_id=user.id,
            credential_id=credential_id
        ).first()

        if not credential:
            return jsonify({"ok": False, "message": "Credencial no registrada"}), 401

        # Verificar la autenticación
        verified, new_sign_count = verify_authentication(
            credential_data,
            challenge,
            credential.public_key,
            credential.sign_count,
        )

        if not verified:
            return jsonify({"ok": False, "message": "Autenticación fallida"}), 401

        # Actualizar sign_count y last_used
        credential.sign_count = new_sign_count
        credential.last_used = datetime.utcnow()
        db.session.commit()

        # Crear la sesión
        session["user_id"] = user.id
        session["username"] = user.username
        session.pop("webauthn_auth_challenge", None)
        session.pop("webauthn_auth_username", None)
        session.modified = True

        return jsonify({
            "ok": True,
            "message": "Autenticación correcta",
            "redirect": url_for("web.dashboard")
        }), 200
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 401


@web.route("/webauthn/credentials", methods=["GET"])
@api_login_required
def webauthn_list_credentials():
    """Lista las credenciales WebAuthn del usuario"""
    from models.webauthn_credential import WebauthnCredential

    user = db.session.get(User, session["user_id"])
    if not user:
        return jsonify({"ok": False, "message": "Sesión inválida"}), 401

    credentials = WebauthnCredential.query.filter_by(user_id=user.id).all()

    return jsonify({
        "ok": True,
        "credentials": [c.to_dict() for c in credentials]
    }), 200


@web.route("/webauthn/credentials/<int:credential_id>", methods=["DELETE"])
@api_login_required
def webauthn_delete_credential(credential_id):
    """Elimina una credencial WebAuthn"""
    from models.webauthn_credential import WebauthnCredential

    user = db.session.get(User, session["user_id"])
    if not user:
        return jsonify({"ok": False, "message": "Sesión inválida"}), 401

    credential = WebauthnCredential.query.filter_by(
        id=credential_id,
        user_id=user.id
    ).first()

    if not credential:
        return jsonify({"ok": False, "message": "Credencial no encontrada"}), 404

    db.session.delete(credential)

    # Si no hay más credenciales, desactivar WebAuthn
    remaining = WebauthnCredential.query.filter_by(user_id=user.id).count()
    if remaining == 0:
        user.webauthn_enabled = False

    db.session.commit()

    return jsonify({
        "ok": True,
        "message": "Credencial eliminada"
    }), 200

