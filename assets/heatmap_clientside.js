(function () {
  window.dash_clientside = Object.assign({}, window.dash_clientside, {
    heatmap: {
      download_heatmap: function (n_clicks, selected_team) {
        if (!n_clicks) {
          return '';
        }

        const teamName = (typeof selected_team === 'string' && selected_team) ? selected_team : 'RC Deportivo';
        const captureArea = document.getElementById('heatmap-capture-area');
        if (!captureArea) {
          alert('No se encontró el área de captura.');
          return '';
        }

        function ensureHtml2CanvasLoaded(cb) {
          if (typeof html2canvas === 'function') return cb();
          const existing = document.querySelector('script[src*="html2canvas"]');
          if (existing) {
            existing.addEventListener('load', cb);
            return;
          }
          const script = document.createElement('script');
          script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
          script.onload = cb;
          document.head.appendChild(script);
        }

        function tryCapture(scales) {
          const scale = scales.shift();
          if (!scale) {
            alert('No se pudo generar la imagen (memoria insuficiente).');
            return;
          }

          html2canvas(captureArea, {
            scale: scale, // Alta calidad con fallback
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff',
            logging: false,
            width: captureArea.scrollWidth,
            height: captureArea.scrollHeight,
            windowWidth: document.documentElement.scrollWidth,
            windowHeight: document.documentElement.scrollHeight,
            scrollX: 0,
            scrollY: -window.scrollY
          }).then(function (canvas) {
            canvas.toBlob(function (blob) {
              const url = URL.createObjectURL(blob);
              const link = document.createElement('a');
              link.href = url;
              link.download = teamName.replace(/ /g, '_') + '_Heatmap_Rendimiento.png';
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
              URL.revokeObjectURL(url);
            }, 'image/png');
          }).catch(function (e) {
            console.error('html2canvas error con scale', scale, e);
            tryCapture(scales); // probar siguiente escala
          });
        }

        ensureHtml2CanvasLoaded(function () {
          // Preferir la máxima calidad posible, con degradación si falla
          const base = Math.max(3, (window.devicePixelRatio || 1) * 2);
          const uniqueScales = Array.from(new Set([4, base, 3, 2]));
          tryCapture(uniqueScales);
        });

        return '';
      }
    }
  });
})();
