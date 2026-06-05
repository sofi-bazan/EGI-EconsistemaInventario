# =========================================================
# Inventario ITU — app.py (versión de desarrollo/mock)
#
# Este archivo tiene datos inventados (hardcodeados) en lugar
# de conectarse a MySQL, MongoDB y LDAP. Eso nos permite
# trabajar en el frontend sin necesitar levantar nada más.
#
# Cuando el front esté listo, estas funciones se reemplazan
# por las versiones reales que sí se conectan a las bases de
# datos. La estructura de rutas y templates NO cambia.
# =========================================================

from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)

# La secret_key es necesaria para que Flask pueda cifrar
# la cookie de sesión. En producción esto va en una variable
# de entorno, nunca hardcodeado así.
app.secret_key = 'dev-secret-key-cambiar-en-produccion'

# =========================================================
# DATOS MOCKEADOS
# Simulan lo que vendría de MySQL y MongoDB.
# En el sistema real, estas listas las construye Flask
# haciendo queries a las bases de datos.
# =========================================================

AULAS_MOCK = [
    {'id': 1, 'nombre': 'Lab 1 — Informática'},
    {'id': 2, 'nombre': 'Lab 2 — Redes'},
    {'id': 3, 'nombre': 'Lab 3 — Sistemas'},
    {'id': 4, 'nombre': 'Aula 10 — Teoría'},
]

EQUIPOS_MOCK = [
    {
        'id': 1,
        'numero_serie': 'ITU-2024-001',
        'tipo': 'desktop',
        'edificio': 'Pabellón A',
        'piso': '1',
        'aula': 'Lab 1 — Informática',
        'numero_banco': 3,
        'responsable': 'Lic. García',
        'fecha_alta': '2024-03-01',
        'proximo_mantenimiento': '2025-03-01',
    },
    {
        'id': 2,
        'numero_serie': 'ITU-2024-002',
        'tipo': 'laptop',
        'edificio': 'Pabellón B',
        'piso': '2',
        'aula': 'Lab 2 — Redes',
        'numero_banco': 7,
        'responsable': 'Ing. Pérez',
        'fecha_alta': '2024-05-15',
        'proximo_mantenimiento': '2025-05-15',
    },
    {
        'id': 3,
        'numero_serie': 'ITU-2024-003',
        'tipo': 'desktop',
        'edificio': 'Pabellón A',
        'piso': '1',
        'aula': 'Lab 3 — Sistemas',
        'numero_banco': 1,
        'responsable': 'Lic. Martínez',
        'fecha_alta': '2024-01-10',
        'proximo_mantenimiento': '2025-01-10',
    },
]

# Datos de hardware: el id corresponde al id del equipo en EQUIPOS_MOCK.
# En el sistema real, el link entre las dos bases de datos es ese mismo id.
HARDWARE_MOCK = {
    1: {
        'fabricante': 'Lenovo',
        'modelo': 'ThinkCentre M75q',
        'cpu': 'AMD Ryzen 5 PRO 4650GE @ 3.3GHz',
        'ram_gb': 16,
        'disco_gb': 512,
        'disco_tipo': 'ssd',
        'so': 'Windows 11 Pro 23H2',
        'monitor': 'Samsung 24" Full HD',
        'mouse': True,
        'teclado': True,
    },
    2: {
        'fabricante': 'HP',
        'modelo': 'EliteBook 840 G9',
        'cpu': 'Intel Core i5-1235U @ 1.3GHz',
        'ram_gb': 8,
        'disco_gb': 256,
        'disco_tipo': 'nvme',
        'so': 'Windows 11 Pro 23H2',
        'monitor': 'N/A (laptop)',
        'mouse': False,
        'teclado': True,
    },
    3: {
        'fabricante': 'Dell',
        'modelo': 'OptiPlex 7090',
        'cpu': 'Intel Core i7-10700 @ 2.9GHz',
        'ram_gb': 32,
        'disco_gb': 1024,
        'disco_tipo': 'hdd',
        'so': 'Ubuntu 22.04 LTS',
        'monitor': 'Dell 27" 4K',
        'mouse': True,
        'teclado': True,
    },
}

# =========================================================
# RUTAS
# Cada función de acá corresponde a una URL de la aplicación.
# Flask las conecta usando el decorador @app.route.
# =========================================================

@app.route('/')
def index():
    # Si ya hay sesión activa, mandamos al dashboard.
    # Si no, al login.
    if session.get('username'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    # GET: simplemente mostrar el formulario
    if request.method == 'GET':
        return render_template('login.html')

    # POST: el usuario envió el formulario con usuario y contraseña
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    # En el sistema real, acá haríamos un BIND contra el servidor
    # LDAP para verificar las credenciales. Acá simplemente
    # aceptamos cualquier usuario/contraseña que no esté vacío.
    if username and password:
        session['username'] = username
        flash(f'Bienvenido, {username}', 'success')
        return redirect(url_for('dashboard'))

    flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if not session.get('username'):
        return redirect(url_for('login'))

    # Estadísticas calculadas a partir de los datos mock.
    # En el sistema real, estos números los dan queries a MySQL y MongoDB.
    stats = {
        'total_equipos': len(EQUIPOS_MOCK),
        'total_aulas': len(AULAS_MOCK),
        'mantenimiento_pendiente': 2,
        'total_hardware': len(HARDWARE_MOCK),
    }
    return render_template('dashboard.html', stats=stats)


@app.route('/inventario')
def inventario():
    if not session.get('username'):
        return redirect(url_for('login'))

    # Leemos los filtros que el usuario mandó en la URL
    # (ej: /inventario?aula=Lab+1&responsable=García)
    aula_filtro = request.args.get('aula', '').strip()
    responsable_filtro = request.args.get('responsable', '').strip()

    # Aplicamos los filtros sobre la lista mock.
    # En el sistema real, estos filtros van como condiciones WHERE en MySQL.
    equipos = EQUIPOS_MOCK
    if aula_filtro:
        equipos = [e for e in equipos if aula_filtro.lower() in e['aula'].lower()]
    if responsable_filtro:
        equipos = [e for e in equipos if responsable_filtro.lower() in e['responsable'].lower()]

    return render_template('inventario.html',
                           equipos=equipos,
                           aula_filtro=aula_filtro,
                           responsable_filtro=responsable_filtro)


@app.route('/equipo/<int:equipo_id>')
def detalle_equipo(equipo_id):
    if not session.get('username'):
        return redirect(url_for('login'))

    # Buscamos el equipo por id en la lista mock
    equipo = next((e for e in EQUIPOS_MOCK if e['id'] == equipo_id), None)
    # Buscamos su hardware en el diccionario mock
    hardware = HARDWARE_MOCK.get(equipo_id)

    if not equipo:
        flash('Equipo no encontrado', 'warning')
        return redirect(url_for('inventario'))

    return render_template('detalle_equipo.html', equipo=equipo, hardware=hardware)


@app.route('/equipo/nuevo', methods=['GET', 'POST'])
def nuevo_equipo():
    if not session.get('username'):
        return redirect(url_for('login'))

    if request.method == 'GET':
        return render_template('nuevo_equipo.html', aulas=AULAS_MOCK)

    # POST: guardamos los datos del formulario.
    # En el sistema real, acá haríamos INSERT en MySQL para los datos
    # de ubicación, e insertDoc en MongoDB para el hardware.
    # Por ahora solo simulamos que funcionó.
    numero_serie = request.form.get('numero_serie', '').strip()
    flash(f'Equipo {numero_serie} registrado correctamente (mock)', 'success')
    return redirect(url_for('inventario'))


@app.route('/equipo/<int:equipo_id>/eliminar', methods=['POST'])
def eliminar_equipo(equipo_id):
    if not session.get('username'):
        return redirect(url_for('login'))

    # En el sistema real: DELETE en MySQL + deleteOne en MongoDB.
    equipo = next((e for e in EQUIPOS_MOCK if e['id'] == equipo_id), None)
    if equipo:
        flash(f'Equipo {equipo["numero_serie"]} eliminado (mock)', 'success')
    return redirect(url_for('inventario'))


@app.route('/api/equipos')
def api_equipos():
    # Endpoint que devuelve JSON en lugar de HTML.
    # Útil para verificar que los datos llegan bien desde el front.
    from flask import jsonify
    return jsonify(EQUIPOS_MOCK)


# =========================================================
# Punto de entrada: solo se ejecuta cuando corrés
# `python app.py` directamente. No se ejecuta cuando
# lo levanta Gunicorn (el servidor de producción en Docker).
# =========================================================
if __name__ == '__main__':
    # debug=True hace que Flask se reinicie automáticamente
    # cada vez que guardás un cambio en el código.
    app.run(debug=True, host='0.0.0.0', port=5000)
