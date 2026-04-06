from utils.biometric_base import WebAuthnProvider


class BiometricAuthService:
    """Facade para centralizar reglas de biometria y facilitar futuras extensiones."""

    def __init__(self):
        self.webauthn_provider = WebAuthnProvider()

    def login_allowed(self, user) -> tuple[bool, str]:
        if not user:
            return False, "Usuario no encontrado"
        if not user.webauthn_enabled:
            return False, "Usuario no tiene WebAuthn configurado"
        if not user.biometric_login_enabled:
            return False, "El usuario desactivo el login biometrico"
        return True, "OK"

    def capabilities(self, user) -> dict:
        return {
            "webauthn_registered": bool(user and user.webauthn_enabled),
            "biometric_login_enabled": bool(user and user.biometric_login_enabled),
            "future_providers": {
                "face_recognition": "pending",
                "gait_recognition": "pending",
                "full_body_detection": "pending",
            },
        }

