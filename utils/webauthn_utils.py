"""
Utilidades para manejar WebAuthn/Passkeys
"""

from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.structs import (
    UserVerificationRequirement,
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    PublicKeyCredentialType,
)
from webauthn.helpers.cose import COSEAlgorithmIdentifier
from webauthn import (
    generate_registration_options as webauthn_gen_reg_options,
    verify_registration_response as webauthn_verify_reg,
    generate_authentication_options as webauthn_gen_auth_options,
    verify_authentication_response as webauthn_verify_auth,
)
import json
import os

def get_webauthn_config() -> tuple[str, str, str]:
    """Resuelve la configuracion WebAuthn segun APP_ENV."""
    app_env = os.getenv("APP_ENV", "development").strip().lower()
    rp_name = os.getenv("RP_NAME", "MiAppFlask")

    if app_env == "production":
        rp_id = os.getenv("RP_ID", "danielgomezgo.com")
        origin = os.getenv("ORIGIN", "https://danielgomezgo.com")
    else:
        rp_id = os.getenv("DEV_RP_ID", "localhost")
        origin = os.getenv("DEV_ORIGIN", "http://localhost:8000")

    return rp_id, rp_name, origin


def generate_registration_options(username: str, user_id: str):
    """
    Genera las opciones para registrar una credencial WebAuthn
    """
    try:
        rp_id, rp_name, _ = get_webauthn_config()
        opts = webauthn_gen_reg_options(
            rp_id=rp_id,
            rp_name=rp_name,
            user_id=str(user_id).encode("utf-8"),
            user_name=username,
            user_display_name=username,
            supported_pub_key_algs=[
                COSEAlgorithmIdentifier.ECDSA_SHA_256,
                COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
            ],
            authenticator_selection=AuthenticatorSelectionCriteria(
                authenticator_attachment=AuthenticatorAttachment.PLATFORM,
                user_verification=UserVerificationRequirement.PREFERRED,
            ),
        )
        return opts
    except Exception as e:
        print(f"❌ Error en generate_registration_options: {str(e)}")
        raise Exception(f"Error generando opciones de registro: {str(e)}")


def verify_registration(credential_data: dict, challenge: str, user_id: str):
    """
    Verifica la credencial de registro WebAuthn
    """
    try:
        rp_id, _, origin = get_webauthn_config()
        expected_challenge = base64url_to_bytes(challenge)

        verification = webauthn_verify_reg(
            credential=credential_data,
            expected_challenge=expected_challenge,
            expected_origin=origin,
            expected_rp_id=rp_id,
        )

        credential_id = bytes_to_base64url(verification.credential_id)
        public_key = json.dumps({
            "key": bytes_to_base64url(verification.credential_public_key),
        })

        return True, public_key, credential_id, verification.sign_count
    except Exception as e:
        print(f"❌ Error en verify_registration: {str(e)}")
        raise Exception(f"Verificación de registro fallida: {str(e)}")


def generate_authentication_options(credential_ids: list[str] | None = None):
    """
    Genera las opciones para autenticarse con WebAuthn
    """
    try:
        rp_id, _, _ = get_webauthn_config()
        allow_credentials = None
        if credential_ids:
            allow_credentials = [
                PublicKeyCredentialDescriptor(
                    id=base64url_to_bytes(credential_id),
                    type=PublicKeyCredentialType.PUBLIC_KEY,
                )
                for credential_id in credential_ids
            ]

        opts = webauthn_gen_auth_options(
            rp_id=rp_id,
            user_verification=UserVerificationRequirement.PREFERRED,
            allow_credentials=allow_credentials,
        )
        return opts
    except Exception as e:
        print(f"❌ Error en generate_authentication_options: {str(e)}")
        raise Exception(f"Error generando opciones de autenticación: {str(e)}")


def verify_authentication(
    credential_data: dict,
    challenge: str,
    stored_public_key: str,
    sign_count: int,
):
    """
    Verifica la credencial de autenticación WebAuthn
    """
    try:
        rp_id, _, origin = get_webauthn_config()
        expected_challenge = base64url_to_bytes(challenge)

        pk_data = json.loads(stored_public_key)
        public_key_bytes = base64url_to_bytes(pk_data["key"])

        verification = webauthn_verify_auth(
            credential=credential_data,
            expected_challenge=expected_challenge,
            expected_origin=origin,
            expected_rp_id=rp_id,
            credential_public_key=public_key_bytes,
            credential_current_sign_count=sign_count,
        )

        return True, verification.new_sign_count
    except Exception as e:
        print(f"❌ Error en verify_authentication: {str(e)}")
        raise Exception(f"Verificación de autenticación fallida: {str(e)}")
