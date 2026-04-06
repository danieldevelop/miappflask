# MiAppFlask

Aplicacion Flask con autenticacion por password, TOTP y WebAuthn (huella/cara del dispositivo).

## Fase 2 y 2.1 implementadas

- **Fase 2**: base desacoplada para biometria futura en `utils/biometric_base.py` y `utils/biometric_service.py`.
- **Fase 2.1**:
  - Auditoria de accesos en `models/auth_event.py`.
  - Toggle por usuario para permitir/bloquear login biometrico (`/webauthn/login-toggle`).
  - Endpoint de ultimos accesos (`/auth-events/recent`).
  - Panel dashboard con hoja de ruta biometrica y lista de eventos recientes.

## Fase 2.2 Reconocimiento Facial

- **Fase 2.2A**: Captura de cámara + detección facial en tiempo real (MediaPipe).
- **Fase 2.2B**: Login por reconocimiento facial (comparación de embeddings).
  - `models/facial_embedding.py`: almacena embeddings faciales (468D).
  - `utils/facial_detection.py`: MediaPipe + liveness detection + comparación.
  - `POST /facial/detect-frame`: detección en tiempo real.
  - `POST /facial/register-embedding`: registra rostro del usuario.
  - `POST /facial/authenticate-frame`: login por facial recognition.
  - UI en login con pestaña "📹 Reconocimiento Facial".
- **Fase 2.2C**: Registro y gestión de múltiples rostros en dashboard.
  - `GET /facial/embeddings`: lista rostros del usuario.
  - `DELETE /facial/embeddings/<id>`: elimina rostro.
  - Panel en dashboard: captura + lista + eliminar.
  - Soporte para múltiples rostros del mismo usuario.

## Variables de entorno clave

- `APP_ENV=development` para local con `localhost`.
- `APP_ENV=production` para dominio publico.
- `DEV_RP_ID`, `DEV_ORIGIN`, `RP_ID`, `ORIGIN` para WebAuthn.

## Smoke test rapido

```powershell
python scripts/smoke_auth_phase21.py
```
