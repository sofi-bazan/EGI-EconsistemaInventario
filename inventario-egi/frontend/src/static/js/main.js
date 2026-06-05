/* =========================================================
   Inventario ITU — JavaScript global
   Este archivo se carga en todas las páginas a través de
   base.html. Cada sección está comentada para que sea fácil
   encontrar qué hace cada parte.
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {

    /* ----- Confirmación antes de eliminar un equipo -----
       Los botones de eliminar tienen el atributo
       data-confirm con el mensaje a mostrar.
       Si el usuario cancela, se detiene el envío del form. */
    document.querySelectorAll('form[data-confirm]').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            var mensaje = form.getAttribute('data-confirm');
            if (!confirm(mensaje)) {
                e.preventDefault(); // cancela el envío
            }
        });
    });

    /* ----- Auto-cerrar alertas flash después de 4 segundos -----
       Las alertas de éxito/error que Flask manda con flash()
       desaparecen solas para no molestar al usuario. */
    document.querySelectorAll('.alert').forEach(function (alerta) {
        setTimeout(function () {
            // Bootstrap tiene su propio método para cerrar alertas
            var bsAlert = bootstrap.Alert.getOrCreateInstance(alerta);
            bsAlert.close();
        }, 4000);
    });

    /* ----- Marcar fila activa en la tabla de inventario -----
       Cuando el usuario hace click en una fila de la tabla,
       la resalta visualmente para indicar selección. */
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
