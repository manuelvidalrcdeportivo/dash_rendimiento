function updateBodyClass(path) {
    if (path === "/") {
        document.body.classList.add('login-mode');
        document.body.classList.remove('dashboard-mode');
    } else {
        document.body.classList.add('dashboard-mode');
        document.body.classList.remove('login-mode');
    }
}

// Ejecutar al cargar por primera vez
window.addEventListener('DOMContentLoaded', function () {
    updateBodyClass(window.location.pathname);
});

// Reaccionar a cambios de navegación internos de Dash
window.addEventListener('popstate', function () {
    updateBodyClass(window.location.pathname);
});

// Para cambios por dcc.Link (Dash no siempre dispara popstate)
const observer = new MutationObserver(function () {
    updateBodyClass(window.location.pathname);
});
observer.observe(document.body, { childList: true, subtree: true });
