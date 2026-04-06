const showAlert = (title, text, icon) => Swal.fire({ title, text, icon, });

const showAlertToast = (icon, title) => {
    Swal.mixin({
        toast: true,
        position: "top",
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.onmouseenter = Swal.stopTimer;
            toast.onmouseleave = Swal.resumeTimer;
        }
    }).fire({
        icon,
        title,
    });
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
    showAlert,
    showAlertToast,
    validateUsername,
    validatePassword,
}