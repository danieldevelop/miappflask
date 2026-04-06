"use strict"

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
            return showError(data.message || "Error al iniciar sesion");
        }

        showSuccess(data.message || "Login correcto");

        // Opcional: redireccion
        if (data.redirect) window.location.href = data.redirect;
    } catch (error) {
        showError("No se pudo conectar con el servidor");
        console.error(error);
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
            alert(data.message || "No se pudo cerrar sesión");
            return;
        }

        if (data.redirect) {
            window.location.href = data.redirect;
        }
    } catch (error) {
        console.error("Error al cerrar sesión:", error);
        alert("No se pudo conectar con el servidor");
    }
};

export {
    authenticateUser,
    logoutUser,
}