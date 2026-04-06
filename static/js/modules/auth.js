"use strict"

import { showAlertToast } from "./utils.js";

const authenticateUser = async (usuario, clave, remember, showError, showSuccess) => {
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

        showAlertToast("success", data.message || "Login correcto");

        if (data.redirect) window.location.href = data.redirect;
    } catch (error) {
        showAlertToast("error", "No se pudo conectar con el servidor");
    }
}

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
    logoutUser,
}