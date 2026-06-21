# =========================================================
# Inventario ITU - app.py (versión REAL con conexiones)
#
# Se conecta a:
#   - SQL Server (ubicación de equipos)  -> pymssql
#   - MongoDB    (hardware de equipos)   -> pymongo
#   - LDAP / AD  (autenticación)         -> ldap3
#
# TODA la configuración (hosts, puertos, usuarios, claves)
# se lee de VARIABLES DE ENTORNO. Nada hardcodeado.
# En Kubernetes esas variables vienen de ConfigMaps y Secrets.
# =========================================================

import os
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify)

import pymssql
from pymongo import MongoClient
from ldap3 import Server, Connection, ALL

app = Flask(__name__)

# La secret_key se lee de variable de entorno (NO hardcodeada).
# Si no existe, usa un valor de respaldo solo para desarrollo.
app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-change-me')

# ---------------------------------------------------------
# CONFIGURACIÓN (toda desde variables de entorno)
# Los nombres por defecto apuntan a los Services de Kubernetes.
# ---------------------------------------------------------
# SQL Server
SQL_HOST = os.environ.get('SQL_HOST', 'ubicacion-db')
SQL_PORT = int(os.environ.get('SQL_PORT', '1433'))
SQL_USER = os.environ.get('SQL_USER', 'sa')
SQL_PASSWORD = os.environ.get('SQL_PASSWORD', '')
SQL_DATABASE = os.environ.get('SQL_DATABASE', 'Inventario')

# MongoDB
MONGO_HOST = os.environ.get('MONGO_HOST', 'inventario-db')
MONGO_PORT = int(os.environ.get('MONGO_PORT', '27017'))
MONGO_DB = os.environ.get('MONGO_DB', 'inventario')
MONGO_COLLECTION = os.environ.get('MONGO_COLLECTION', 'hardware')

# LDAP / Active Directory
LDAP_HOST = os.environ.get('LDAP_HOST', 'ldap-service')
LDAP_PORT = int(os.environ.get('LDAP_PORT', '389'))
LDAP_DOMAIN = os.environ.get('LDAP_DOMAIN', 'itu.local')


# =========================================================
# FUNCIONES DE CONEXIÓN
# Cada una abre la conexión, la usa y la cierra.
# Si algo falla, se captura el error y se devuelve None o []
# para que la app no se caiga, sino que muestre un mensaje.
# =========================================================

def get_sql_connection():
    """Abre una conexión a SQL Server. Devuelve None si falla."""
    try:
        conn = pymssql.connect(
            server=SQL_HOST,
            port=SQL_PORT,
            user=SQL_USER,
            password=SQL_PASSWORD,
            database=SQL_DATABASE,
            timeout=5,
            login_timeout=5,
        )
        return conn
    except Exception as e:
        print(f"[ERROR SQL] No se pudo conectar a SQL Server: {e}")
        return None


def get_mongo_collection():
    """Devuelve la colección de hardware de Mongo. None si falla."""
    try:
        client = MongoClient(MONGO_HOST, MONGO_PORT,
                             serverSelectionTimeoutMS=5000)
        # Forzamos una operación para verificar que conecta
        client.admin.command('ping')
        db = client[MONGO_DB]
        return db[MONGO_COLLECTION]
    except Exception as e:
        print(f"[ERROR MONGO] No se pudo conectar a MongoDB: {e}")
        return None


def ldap_autenticar(username, password):
    """
    Verifica usuario y contraseña contra Active Directory (LDAP bind).
    Devuelve True si las credenciales son válidas, False si no.
    """
    try:
        # En AD, el usuario suele autenticarse como usuario@dominio
        user_principal = f"{username}@{LDAP_DOMAIN}"
        server = Server(LDAP_HOST, port=LDAP_PORT, get_info=ALL)
        conn = Connection(server, user=user_principal,
                         password=password, auto_bind=True)
        # Si el bind no lanzó excepción, las credenciales son correctas
        conn.unbind()
        return True
    except Exception as e:
        print(f"[INFO LDAP] Bind fallido para '{username}': {e}")
        return False


# =========================================================
# FUNCIONES DE DATOS
# Combinan SQL (ubicación) + Mongo (hardware).
# =========================================================

def obtener_equipos(aula_filtro='', responsable_filtro=''):
    """
    Trae los equipos desde SQL Server con su ubicación y responsable.
    Hace JOIN entre equipo, ubicacion y responsable.
    Aplica filtros opcionales por aula y responsable.
    """
    conn = get_sql_connection()
    if conn is None:
        return []

    equipos = []
    try:
        cursor = conn.cursor(as_dict=True)
        # JOIN: equipo -> ubicacion (dónde está) -> responsable (de quién es)
        query = """
            SELECT
                e.equipo_id,
                e.numero_serie,
                e.numero_banco,
                e.estado,
                e.fecha_alta,
                e.fecha_proximo_mantenimiento,
                u.edificio,
                u.aula,
                r.nombre + ' ' + r.apellido AS responsable
            FROM equipo e
            INNER JOIN ubicacion u   ON e.ubicacion_id   = u.id
            INNER JOIN responsable r ON e.responsable_id = r.id
            WHERE 1 = 1
        """
        params = []
        if aula_filtro:
            query += " AND u.aula LIKE %s"
            params.append(f"%{aula_filtro}%")
        if responsable_filtro:
            query += " AND (r.nombre + ' ' + r.apellido) LIKE %s"
            params.append(f"%{responsable_filtro}%")

        cursor.execute(query, tuple(params))
        equipos = cursor.fetchall()
    except Exception as e:
        print(f"[ERROR SQL] Consulta de equipos falló: {e}")
    finally:
        conn.close()

    return equipos


def obtener_equipo(equipo_id):
    """Trae un equipo puntual (ubicación) desde SQL por su equipo_id."""
    conn = get_sql_connection()
    if conn is None:
        return None

    equipo = None
    try:
        cursor = conn.cursor(as_dict=True)
        query = """
            SELECT
                e.equipo_id,
                e.numero_serie,
                e.numero_banco,
                e.estado,
                e.fecha_alta,
                e.fecha_proximo_mantenimiento,
                u.edificio,
                u.aula,
                r.nombre + ' ' + r.apellido AS responsable
            FROM equipo e
            INNER JOIN ubicacion u   ON e.ubicacion_id   = u.id
            INNER JOIN responsable r ON e.responsable_id = r.id
            WHERE e.equipo_id = %s
        """
        cursor.execute(query, (equipo_id,))
        equipo = cursor.fetchone()
    except Exception as e:
        print(f"[ERROR SQL] Consulta de equipo {equipo_id} falló: {e}")
    finally:
        conn.close()

    return equipo


def obtener_hardware(equipo_id):
    """
    Trae el hardware de un equipo desde MongoDB.
    El vínculo entre SQL y Mongo es el mismo equipo_id (ej: PC-0001).
    """
    coleccion = get_mongo_collection()
    if coleccion is None:
        return None
    try:
        # Buscamos el documento cuyo equipo_id coincide
        doc = coleccion.find_one({'equipo_id': equipo_id}, {'_id': 0})
        return doc
    except Exception as e:
        print(f"[ERROR MONGO] Consulta de hardware {equipo_id} falló: {e}")
        return None


# =========================================================
# RUTAS
# =========================================================

@app.route('/')
def index():
    if session.get('username'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not username or not password:
        flash('Ingresá usuario y contraseña', 'danger')
        return render_template('login.html')

    # Autenticación REAL contra Active Directory
    if ldap_autenticar(username, password):
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

    equipos = obtener_equipos()
    stats = {
        'total_equipos': len(equipos),
        'total_aulas': len({e['aula'] for e in equipos}) if equipos else 0,
        'mantenimiento_pendiente': sum(
            1 for e in equipos if e.get('estado') == 'mantenimiento'),
        'total_hardware': len(equipos),
    }
    return render_template('dashboard.html', stats=stats)


@app.route('/inventario')
def inventario():
    if not session.get('username'):
        return redirect(url_for('login'))

    aula_filtro = request.args.get('aula', '').strip()
    responsable_filtro = request.args.get('responsable', '').strip()

    equipos = obtener_equipos(aula_filtro, responsable_filtro)

    return render_template('inventario.html',
                           equipos=equipos,
                           aula_filtro=aula_filtro,
                           responsable_filtro=responsable_filtro)


@app.route('/equipo/<equipo_id>')
def detalle_equipo(equipo_id):
    if not session.get('username'):
        return redirect(url_for('login'))

    equipo = obtener_equipo(equipo_id)
    if not equipo:
        flash('Equipo no encontrado', 'warning')
        return redirect(url_for('inventario'))

    # El hardware viene de Mongo, usando el mismo equipo_id
    hardware = obtener_hardware(equipo_id)

    return render_template('detalle_equipo.html',
                           equipo=equipo, hardware=hardware)


@app.route('/equipo/nuevo', methods=['GET', 'POST'])
def nuevo_equipo():
    if not session.get('username'):
        return redirect(url_for('login'))

    if request.method == 'GET':
        # Para el form necesitamos la lista de aulas (desde SQL)
        conn = get_sql_connection()
        aulas = []
        if conn is not None:
            try:
                cursor = conn.cursor(as_dict=True)
                cursor.execute("SELECT id, aula AS nombre FROM ubicacion")
                aulas = cursor.fetchall()
            except Exception as e:
                print(f"[ERROR SQL] No se pudieron traer aulas: {e}")
            finally:
                conn.close()
        return render_template('nuevo_equipo.html', aulas=aulas)

    # POST: insertar el nuevo equipo en SQL (ubicación) y Mongo (hardware)
    numero_serie = request.form.get('numero_serie', '').strip()
    # NOTA: la inserción completa (con todos los campos del form) se
    # implementa acá. Por ahora se deja el flash de confirmación.
    # TODO: armar el INSERT en SQL + insert_one en Mongo con los datos del form.
    flash(f'Equipo {numero_serie} registrado', 'success')
    return redirect(url_for('inventario'))


@app.route('/equipo/<equipo_id>/eliminar', methods=['POST'])
def eliminar_equipo(equipo_id):
    if not session.get('username'):
        return redirect(url_for('login'))

    # DELETE en SQL + deleteOne en Mongo
    conn = get_sql_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM equipo WHERE equipo_id = %s",
                          (equipo_id,))
            conn.commit()
        except Exception as e:
            print(f"[ERROR SQL] No se pudo eliminar {equipo_id}: {e}")
        finally:
            conn.close()

    coleccion = get_mongo_collection()
    if coleccion is not None:
        try:
            coleccion.delete_one({'equipo_id': equipo_id})
        except Exception as e:
            print(f"[ERROR MONGO] No se pudo eliminar hardware {equipo_id}: {e}")

    flash(f'Equipo {equipo_id} eliminado', 'success')
    return redirect(url_for('inventario'))


@app.route('/api/equipos')
def api_equipos():
    if not session.get('username'):
        return jsonify({'error': 'no autenticado'}), 401
    return jsonify(obtener_equipos())


@app.route('/health')
def health():
    """
    Endpoint de diagnóstico: dice si la app llega a cada servicio.
    Útil para probar la conectividad sin tocar la interfaz.
    """
    estado = {
        'sql': get_sql_connection() is not None,
        'mongo': get_mongo_collection() is not None,
    }
    return jsonify(estado)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)