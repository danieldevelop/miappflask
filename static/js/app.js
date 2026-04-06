"use strict";

import { authenticateUser, logoutUser } from "./modules/auth.js";
import { hiddenMessage, validateUsername, validatePassword } from "./modules/utils.js";

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

        const showError = (text) => {
            if (!message) return;
            message.textContent = text;
            message.classList.remove("success");
            message.classList.add("error");
            hiddenMessage(message, 3000);
        };

        const showSuccess = (text) => {
            if (!message) return;
            message.textContent = text;
            message.classList.remove("error");
            message.classList.add("success");
            hiddenMessage(message, 3000);
        };

        if (!usuario) return showError("El campo Usuario no puede estar vacio");
        if (!clave) return showError("El campo Contraseña no puede estar vacio");
        if (!validateUsername(usuario)) return showError("El campo Usuario no puede contener caracteres especiales, solo un punto, guion o guion bajo");
        if (!validatePassword(clave)) return showError("El campo Contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número");

        await authenticateUser(usuario, clave, remember, showError, showSuccess);
    });
}

const btnLogout = document.querySelector("#btn-logout");

if (btnLogout) {
    btnLogout.addEventListener("click", async () => {
        await logoutUser();
    });
}


