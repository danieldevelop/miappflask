from abc import ABC, abstractmethod


class BiometricProvider(ABC):
    """Contrato base para proveedores biometricos futuros (face/gait/body)."""

    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def is_enabled_for_user(self, user) -> bool:
        raise NotImplementedError


class WebAuthnProvider(BiometricProvider):
    def provider_name(self) -> str:
        return "webauthn"

    def is_enabled_for_user(self, user) -> bool:
        return bool(user and user.webauthn_enabled and user.biometric_login_enabled)

