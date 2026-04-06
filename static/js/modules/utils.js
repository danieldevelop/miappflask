const hiddenMessage = (message, duration) => {
     setTimeout((e) => {
        message.textContent = "";
        message.classList.remove("error");
    }, duration);
}

// Username: letras, números, punto, guion y guion bajo
const validateUsername = (input) => {
    const usernameRegex = /^[a-zA-Z0-9._-]+$/;
    return usernameRegex.test(input);
};

// Password: mínimo 8, 1 mayúscula, 1 minúscula, 1 número
const validatePassword = (input) => {
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
    return passwordRegex.test(input);
};

export {
    hiddenMessage,
    validateUsername,
    validatePassword,
}