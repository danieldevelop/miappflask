"use strict";

import { authenticateUser, logoutUser, enableTotp, verifyTotpCode } from "./modules/auth.js";
import {validateUsername, validatePassword, showAlertToast} from "./modules/utils.js";

let fullYear = String(new Date().getFullYear()); // Obtengo el año actual para mostrarlo en el footer

document.addEventListener("DOMContentLoaded", () =>
{
    document.getElementById("year").textContent = fullYear;
});

/**
 * Envio de datos al backend del formulario login
 *
 * 1.- Se validan los datos que no venga vacios (por sepárado)
 * 2.- Se valida que el username no tenga caracteres especiales, solo un punto, guion o guion bajo
 * 3.- Se valida que el password tenga al menos 8 caracteres, una mayúscula, una minúscula y un número
 * 4.- Si todo es correcto se envía el formulario
 * 5.- Si hay algún error se muestra un mensaje de error
 *
 * @param {Event} event - El evento del formulario
 * @returns {void}
 */
const formLogin = document.querySelector("#form-login");

if (formLogin) {
    formLogin.addEventListener("submit", async (e) => {
        e.preventDefault();

        const usuario = document.querySelector("#username")?.value.trim() || "";
        const clave = document.querySelector("#password")?.value.trim() || "";
        const remember = document.querySelector("#remember")?.checked || false;
        const message = document.querySelector("#message");

        if (!usuario) return showAlertToast("error", "El campo Usuario no puede estar vacio");
        if (!clave) return showAlertToast("error", "El campo Contraseña no puede estar vacio");
        if (!validateUsername(usuario)) return showAlertToast("error", "El campo Usuario solo puede contener letras, números, puntos, guiones o guiones bajos");
        if (!validatePassword(clave)) return showAlertToast("error", "La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número");

        await authenticateUser(usuario, clave, remember);
    });
}


if (form2fa) {
    form2fa.addEventListener("submit", async (e) => {
        e.preventDefault();

        const code = document.querySelector("#code")?.value.trim() || "";

        if (!code) return showAlertToast("error","Debes ingresar el codigo TOTP");
        await verifyTotpCode(code);
    });
}

if (formTotpSetup) {
    formTotpSetup.addEventListener("submit", async (e) => {
        e.preventDefault();

        const code = document.querySelector("#totp-setup-code")?.value.trim() || "";

        if (!code) return showAlertToast("error", "Debes ingresar el codigo para activar 2FA");
        await enableTotp(code);
    });
}

const btnLogout = document.querySelector("#btn-logout");

if (btnLogout) {
    btnLogout.addEventListener("click", async () => {
        await logoutUser();
    });
}

const btnLogoutClosed = document.querySelector("#btn-logout-closed");

if (btnLogoutClosed) {
    btnLogoutClosed.addEventListener("click", async () => {
        await logoutUser();
    });
}


