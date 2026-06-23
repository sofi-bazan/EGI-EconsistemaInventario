/* =========================================================
   Inventario ITU — JavaScript global
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

    /* ----- Auto-cerrar alertas flash ----- */
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

            if (e.target.closest('.btn')) return;

            document.querySelectorAll('table tbody tr').forEach(function (f) {
                f.classList.remove('table-active');
            });

            fila.classList.add('table-active');
        });
    });

});
