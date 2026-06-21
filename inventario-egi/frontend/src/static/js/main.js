/* =========================================================
   Inventario ITU — JavaScript global
   Este archivo se carga en todas las páginas a través de base.html.
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {

    /* ----- Confirmación antes de eliminar un equipo ----- */
    document.querySelectorAll('form[data-confirm]').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            var mensaje = form.getAttribute('data-confirm');
            if (!confirm(mensaje)) {
                e.preventDefault(); // cancela el envío
            }
        });
    });

    /* ----- Auto-cerrar alertas flash después de 4 segundos ----- */
    document.querySelectorAll('.alert').forEach(function (alerta) {
        setTimeout(function () {
            // Bootstrap tiene su propio método para cerrar alertas
            var bsAlert = bootstrap.Alert.getOrCreateInstance(alerta);
            bsAlert.close();
        }, 4000);
    });

    /* ----- Marcar fila activa en la tabla de inventario ----- */
    document.querySelectorAll('table tbody tr').forEach(function (fila) {
        fila.style.cursor = 'pointer';
        fila.addEventListener('click', function (e) {
            // Si el click fue en un botón de acción, no hacemos nada
            // (deja que el botón maneje su propio evento)
            if (e.target.closest('.btn')) return;

            // Quitamos la selección de cualquier otra fila
            document.querySelectorAll('table tbody tr').forEach(function (f) {
                f.classList.remove('table-active');
            });
            // Marcamos la fila clickeada
            fila.classList.add('table-active');
        });
    });

});
