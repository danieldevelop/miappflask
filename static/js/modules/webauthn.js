/**
 * Módulo para manejar WebAuthn/Passkeys
 */

class WebAuthnManager {
    constructor() {
        this.challenge = null;
    }

    async _parseApiResponse(response) {
        const contentType = response.headers.get("content-type") || "";
        if (contentType.includes("application/json")) {
            return await response.json();
        }

        const text = await response.text();
        if (text.trim().startsWith("<!doctype") || text.trim().startsWith("<html")) {
            throw new Error("El servidor devolvio HTML en lugar de JSON. Revisa la terminal de Flask.");
        }

        throw new Error("Respuesta inesperada del servidor.");
    }

    /**
     * Inicia el registro de una nueva credencial biométrica
     */
    async startRegistration(deviceName = "Mi dispositivo") {
        try {
            // 1. Obtener opciones del servidor
            const optionsResponse = await fetch("/webauthn/register-options", {
                method: "GET",
                headers: { "Content-Type": "application/json" }
            });

            if (!optionsResponse.ok) {
                const error = await this._parseApiResponse(optionsResponse);
                throw new Error(error.message);
            }

            const data = await this._parseApiResponse(optionsResponse);
            const options = data.options;

            console.log("Opciones de registro:", options);

            // 2. Convertir strings base64url a ArrayBuffer
            options.challenge = this._base64urlToBuffer(options.challenge);
            options.user.id = this._base64urlToBuffer(options.user.id);

            // 3. Solicitar credencial al navegador/dispositivo
            const credential = await navigator.credentials.create({
                publicKey: options
            });

            if (!credential) {
                throw new Error("No se completó el registro biométrico");
            }

            // 4. Enviar al servidor para verificación
            const verifyResponse = await fetch("/webauthn/register-verify", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    credential: this._credentialToJSON(credential),
                    device_name: deviceName
                })
            });

            if (!verifyResponse.ok) {
                const error = await this._parseApiResponse(verifyResponse);
                throw new Error(error.message);
            }

            return await this._parseApiResponse(verifyResponse);
        } catch (error) {
            console.error("Error en registro WebAuthn:", error);
            throw error;
        }
    }

    /**
     * Inicia la autenticación con biometría
     */
    async startAuthentication(username) {
        try {
            // 1. Obtener opciones del servidor
            const optionsResponse = await fetch("/webauthn/authenticate-options", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username })
            });

            if (!optionsResponse.ok) {
                const error = await this._parseApiResponse(optionsResponse);
                throw new Error(error.message);
            }

            const data = await this._parseApiResponse(optionsResponse);
            const options = data.options;

            console.log("Opciones de autenticación:", options);

            // 2. Convertir challenge
            options.challenge = this._base64urlToBuffer(options.challenge);

            // 2.1 Convertir allowCredentials[*].id a ArrayBuffer (requerido por WebAuthn API)
            const allowCreds = options.allowCredentials || options.allow_credentials;
            if (Array.isArray(allowCreds)) {
                for (const cred of allowCreds) {
                    if (cred && typeof cred.id === "string") {
                        cred.id = this._base64urlToBuffer(cred.id);
                    }
                }
                // Mantener forma camelCase usada por el navegador
                options.allowCredentials = allowCreds;
                delete options.allow_credentials;
            }

            // 3. Obtener aserción del navegador/dispositivo
            const assertion = await navigator.credentials.get({
                publicKey: options,
                mediation: "optional"
            });

            if (!assertion) {
                throw new Error("Autenticación cancelada");
            }

            // 4. Enviar al servidor para verificación
            const verifyResponse = await fetch("/webauthn/authenticate-verify", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    credential: this._assertionToJSON(assertion)
                })
            });

            if (!verifyResponse.ok) {
                const error = await this._parseApiResponse(verifyResponse);
                throw new Error(error.message);
            }

            return await this._parseApiResponse(verifyResponse);
        } catch (error) {
            console.error("Error en autenticación WebAuthn:", error);
            throw error;
        }
    }

    /**
     * Convierte base64url string a ArrayBuffer
     */
    _base64urlToBuffer(base64url) {
        const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
        const padLen = (4 - (base64.length % 4)) % 4;
        const padded = base64 + '='.repeat(padLen);
        const binary = atob(padded);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return bytes.buffer;
    }

    /**
     * Convierte ArrayBuffer a base64url string
     */
    _bufferToBase64url(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        const base64 = btoa(binary);
        return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
    }

    /**
     * Convierte Credential a JSON serializable
     */
    _credentialToJSON(credential) {
        const attestationObject = this._bufferToBase64url(credential.response.attestationObject);
        const clientDataJSON = this._bufferToBase64url(credential.response.clientDataJSON);

        return {
            type: credential.type,
            id: credential.id,
            rawId: this._bufferToBase64url(credential.rawId),
            response: {
                attestationObject,
                clientDataJSON
            }
        };
    }

    /**
     * Convierte AssertionResponse a JSON serializable
     */
    _assertionToJSON(assertion) {
        return {
            type: assertion.type,
            id: assertion.id,
            rawId: this._bufferToBase64url(assertion.rawId),
            response: {
                clientDataJSON: this._bufferToBase64url(assertion.response.clientDataJSON),
                authenticatorData: this._bufferToBase64url(assertion.response.authenticatorData),
                signature: this._bufferToBase64url(assertion.response.signature),
                userHandle: assertion.response.userHandle ?
                    this._bufferToBase64url(assertion.response.userHandle) : null
            }
        };
    }
}

// Exportar para uso en módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebAuthnManager;
}
