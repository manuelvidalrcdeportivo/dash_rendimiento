(function () {
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js";
    script.onload = () => {
        console.log("html2canvas cargado correctamente");

        document.addEventListener("click", function (e) {
            const boton = e.target.closest("#boton-descargar");
            if (!boton) return;

            const target = document.getElementById("ficha-jugador");
            if (!target) return alert("No se encontró la ficha para capturar");

            html2canvas(target, { scale: 2 }).then(canvas => {
                const link = document.createElement("a");
                link.download = "ficha_jugador.png";
                link.href = canvas.toDataURL("image/png");
                link.click();
            });
        });
    };
    document.head.appendChild(script);
})();
