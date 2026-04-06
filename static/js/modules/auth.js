"use strict"

import { showAlertToast } from "./utils.js";

const authenticateUser = async (usuario, clave, remember) => {
    try {
        const res = await fetch("/login", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                username: usuario,
                password: clave,
                remember_me: remember
            })
        });

        const data = await res.json();

        if (!res.ok || !data.ok) {
            return showAlertToast( "error", data.message || "Error al iniciar sesión");
        }

        if (data.requires_2fa) {
            if (data.redirect) window.location.href = data.redirect;
            return;
        }

        showAlertToast("success", data.message || "Login correcto");

        if (data.redirect) window.location.href = data.redirect;
    } catch (error) {
        showAlertToast("error", "No se pudo conectar con el servidor");
    }
}

const verifyTotpCode = async (code) => {
    try {
        const res = await fetch("/verify-2fa", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ code })
        });

        const data = await res.json();

        if (!res.ok || !data.ok) {
            return showAlertToast("error", data.message || "Codigo TOTP invalido");
        }

        showAlertToast("success", data.message || "Codigo verificado correctamente");

        if (data.redirect) {
            window.location.href = data.redirect;
        }
    } catch (error) {
        showAlertToast("error", "No se pudo conectar con el servidor");
        console.error(error);
    }
};

const enableTotp = async (code) => {
    try {
        const res = await fetch("/2fa/enable", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ code })
        });

        const data = await res.json();

        if (!res.ok || !data.ok) {
            return showAlertToast("error", data.message || "No se pudo activar el 2FA");
        }

        showAlertToast("success", data.message || "2FA activado correctamente");

        if (data.redirect) {
            window.location.href = data.redirect;
        }
    } catch (error) {
        showAlertToast("error", "No se pudo conectar con el servidor");
        console.error(error);
    }
};

const logoutUser = async () => {
    try {
        const res = await fetch("/logout", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            }
        });

        const data = await res.json();

        if (!res.ok || !data.ok) {
            showAlertToast("error", data.message || "No se pudo cerrar sesión");
            return;
        }

        if (data.redirect) {
            window.location.href = data.redirect;
        }
    } catch (error) {
        showAlertToast("error", "No se pudo conectar con el servidor");
    }
};

export {
    authenticateUser,
    verifyTotpCode,
    enableTotp,
    logoutUser,
}