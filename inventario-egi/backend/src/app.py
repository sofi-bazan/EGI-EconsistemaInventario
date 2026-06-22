# =========================================================
# Inventario ITU - app.py
#
# App web Flask (templates Jinja2) del Ecosistema de Inventario Seguro.
# Se conecta a:
#   - SQL Server (ubicacion + propietarios) -> pymssql
#   - MongoDB    (hardware de equipos)      -> pymongo
#   - LDAP / AD  (autenticacion)            -> ldap3
#
# Puente entre SQL y Mongo: el campo equipo_id (ej: 'PC-0001').
# En SQL es la PK (VARCHAR). En Mongo es el campo equipo_id de cada
# documento. Mismo valor en ambos lados = se cruzan los datos.
#
# Toda la config (hosts, puertos, credenciales) viene de variables
# de entorno. Nada hardcodeado.
# =========================================================

import os
from datetime import date

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify)

import pymssql
from pymongo import MongoClient
from ldap3 import Server, Connection, ALL

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-change-me')

# ---------------------------------------------------------
# CONFIGURACION (variables de entorno)
# ---------------------------------------------------------
# SQL Server (Service de K8s: ubicacion-db)
SQL_HOST = os.environ.get('SQL_HOST', 'ubicacion-db')
SQL_PORT = int(os.environ.get('SQL_PORT', '1433'))
SQL_USER = os.environ.get('SQL_USER', 'sa')
SQL_PASSWORD = os.environ.get('SQL_PASSWORD', '')
SQL_DATABASE = os.environ.get('SQL_DATABASE', 'Inventario')

# MongoDB (Service de K8s: inventario-db)
MONGO_HOST = os.environ.get('MONGO_HOST', 'inventario-db')
MONGO_PORT = int(os.environ.get('MONGO_PORT', '27017'))
MONGO_DB = os.environ.get('MONGO_DB', 'inventario')
MONGO_COLLECTION = os.environ.get('MONGO_COLLECTION', 'hardware')
MONGO_USER = os.environ.get('MONGO_USER', '')
MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD', '')

# LDAP / Active Directory (Service de K8s: ldap-service)
LDAP_HOST = os.environ.get('LDAP_HOST', 'ldap-service')
LDAP_PORT = int(os.environ.get('LDAP_PORT', '389'))
LDAP_DOMAIN = os.environ.get('LDAP_DOMAIN', 'itu.local')


# =========================================================
# CONEXIONES
# Cada funcion abre, usa y cierra. Si falla, devuelve None/[]
# y se loguea, para que la app no se caiga sino muestre aviso.
# =========================================================

def get_sql_connection():
    """Abre una conexion a SQL Server. Devuelve None si falla."""
    try:
        return pymssql.connect(
            server=SQL_HOST,
            port=SQL_PORT,
            user=SQL_USER,
            password=SQL_PASSWORD,
            database=SQL_DATABASE,
            timeout=5,
            login_timeout=5,
        )
    except Exception as e:
        print(f"[ERROR SQL] No se pudo conectar a SQL Server: {e}")
        return None


def get_mongo_collection():
    """Devuelve la coleccion de hardware de Mongo. None si falla."""
    try:
        if MONGO_USER:
            uri = (f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}"
                   f"@{MONGO_HOST}:{MONGO_PORT}/")
        else:
            uri = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')   # fuerza verificacion real
        return client[MONGO_DB][MONGO_COLLECTION]
    except Exception as e:
        print(f"[ERROR MONGO] No se pudo conectar a MongoDB: {e}")
        return None


def ldap_autenticar(username, password):
    """
    Verifica usuario/contrasena contra Active Directory (bind LDAP).
    Devuelve True si las credenciales son validas, False si no.
    """
    try:
        user_principal = (username if '@' in username
                          else f"{username}@{LDAP_DOMAIN}")
        server = Server(LDAP_HOST, port=LDAP_PORT, get_info=ALL,
                        connect_timeout=5)
        conn = Connection(server, user=user_principal,
                          password=password, auto_bind=True)
        conn.unbind()
        return True
    except Exception as e:
        print(f"[INFO LDAP] Bind fallido para '{username}': {e}")
        return False


# =========================================================
# HELPERS DE DATOS
# =========================================================

def _hardware_por_equipo():
    """
    Devuelve un dict {equipo_id: documento_hardware} para cruzar
    rapido en el listado del inventario. {} si Mongo no responde.
    """
    coleccion = get_mongo_collection()
    if coleccion is None:
        return {}
    try:
        return {doc['equipo_id']: doc
                for doc in coleccion.find({}, {'_id': 0})}
    except Exception as e:
        print(f"[ERROR MONGO] No se pudo mapear hardware: {e}")
        return {}


def _proximo_equipo_id(conn):
    """
    Calcula el proximo equipo_id con formato PC-XXXX mirando el
    maximo actual en SQL. Asi el puente con Mongo sigue siendo
    legible y estable (PC-0001, PC-0002, ...).
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT MAX(CAST(SUBSTRING(equipo_id, 4, 10) AS INT)) "
            "FROM equipo WHERE equipo_id LIKE 'PC-%'"
        )
        row = cursor.fetchone()
        siguiente = (row[0] or 0) + 1
    except Exception as e:
        print(f"[ERROR SQL] No se pudo calcular proximo id: {e}")
        siguiente = 1
    return f"PC-{siguiente:04d}"


def obtener_equipos(aula_filtro='', responsable_filtro=''):
    """
    Trae equipos desde SQL (ubicacion + responsable) y les agrega el
    'tipo' desde Mongo. Los alias del SELECT coinciden con lo que
    esperan los templates: id, proximo_mantenimiento, etc.
    """
    conn = get_sql_connection()
    if conn is None:
        return []

    equipos = []
    try:
        cursor = conn.cursor(as_dict=True)
        query = """
            SELECT
                e.equipo_id                         AS id,
                e.numero_serie                      AS numero_serie,
                e.numero_banco                      AS numero_banco,
                e.estado                            AS estado,
                e.fecha_alta                        AS fecha_alta,
                e.fecha_proximo_mantenimiento       AS proximo_mantenimiento,
                u.edificio                          AS edificio,
                u.aula                              AS aula,
                (r.nombre + ' ' + r.apellido)       AS responsable
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
        query += " ORDER BY e.equipo_id"

        cursor.execute(query, tuple(params))
        equipos = cursor.fetchall()
    except Exception as e:
        print(f"[ERROR SQL] Consulta de equipos fallo: {e}")
    finally:
        conn.close()

    # El 'tipo' (desktop/laptop) es propiedad del hardware -> Mongo.
    hw_map = _hardware_por_equipo()
    for eq in equipos:
        hw = hw_map.get(eq['id'])
        eq['tipo'] = hw.get('tipo', 'desktop') if hw else 'desktop'

    return equipos


def obtener_equipo(equipo_id):
    """Trae un equipo puntual (ubicacion) desde SQL por su equipo_id."""
    conn = get_sql_connection()
    if conn is None:
        return None

    equipo = None
    try:
        cursor = conn.cursor(as_dict=True)
        query = """
            SELECT
                e.equipo_id                   AS id,
                e.numero_serie                AS numero_serie,
                e.numero_banco                AS numero_banco,
                e.estado                      AS estado,
                e.fecha_alta                  AS fecha_alta,
                e.fecha_proximo_mantenimiento AS proximo_mantenimiento,
                u.edificio                    AS edificio,
                u.aula                        AS aula,
                (r.nombre + ' ' + r.apellido) AS responsable
            FROM equipo e
            INNER JOIN ubicacion u   ON e.ubicacion_id   = u.id
            INNER JOIN responsable r ON e.responsable_id = r.id
            WHERE e.equipo_id = %s
        """
        cursor.execute(query, (equipo_id,))
        equipo = cursor.fetchone()
    except Exception as e:
        print(f"[ERROR SQL] Consulta de equipo {equipo_id} fallo: {e}")
    finally:
        conn.close()

    # 'piso' no existe en el schema; se deja vacio para el template.
    if equipo is not None:
        equipo.setdefault('piso', '—')
    return equipo


def obtener_hardware(equipo_id):
    """
    Trae el hardware de un equipo desde MongoDB.
    El vinculo SQL<->Mongo es el mismo equipo_id (ej: PC-0001).
    """
    coleccion = get_mongo_collection()
    if coleccion is None:
        return None
    try:
        return coleccion.find_one({'equipo_id': equipo_id}, {'_id': 0})
    except Exception as e:
        print(f"[ERROR MONGO] Consulta de hardware {equipo_id} fallo: {e}")
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
        flash('Ingresa usuario y contrasena', 'danger')
        return render_template('login.html')

    if ldap_autenticar(username, password):
        session['username'] = username
        flash(f'Bienvenido, {username}', 'success')
        return redirect(url_for('dashboard'))

    flash('Usuario o contrasena incorrectos', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Sesion cerrada correctamente', 'info')
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
        'total_hardware': len(_hardware_por_equipo()),
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

    hardware = obtener_hardware(equipo_id)
    # El template muestra equipo.tipo; lo tomamos del hardware.
    if hardware:
        equipo['tipo'] = hardware.get('tipo', 'desktop')
    else:
        equipo.setdefault('tipo', 'desktop')

    return render_template('detalle_equipo.html',
                           equipo=equipo, hardware=hardware)


@app.route('/equipo/nuevo', methods=['GET', 'POST'])
def nuevo_equipo():
    if not session.get('username'):
        return redirect(url_for('login'))

    if request.method == 'GET':
        conn = get_sql_connection()
        aulas = []
        if conn is not None:
            try:
                cursor = conn.cursor(as_dict=True)
                cursor.execute(
                    "SELECT id, (edificio + ' - ' + aula) AS nombre "
                    "FROM ubicacion ORDER BY edificio, aula")
                aulas = cursor.fetchall()
            except Exception as e:
                print(f"[ERROR SQL] No se pudieron traer aulas: {e}")
            finally:
                conn.close()
        return render_template('nuevo_equipo.html', aulas=aulas)

    # ----------------- POST: alta real -----------------
    # 1) Datos del form
    numero_serie = request.form.get('numero_serie', '').strip()
    tipo = request.form.get('tipo', 'desktop').strip()
    aula_id = request.form.get('aula_id', '').strip()
    numero_banco = request.form.get('numero_banco', '').strip()
    responsable_nombre = request.form.get('responsable', '').strip()

    if not (numero_serie and aula_id and numero_banco):
        flash('Faltan datos obligatorios de ubicacion', 'danger')
        return redirect(url_for('nuevo_equipo'))

    conn = get_sql_connection()
    if conn is None:
        flash('No se pudo conectar a SQL Server. Equipo no registrado.',
              'danger')
        return redirect(url_for('nuevo_equipo'))

    nuevo_id = None
    try:
        cursor = conn.cursor()

        # 2) Resolver responsable: buscar por "nombre apellido" o usar
        #    el primer tecnico activo como fallback.
        responsable_id = None
        if responsable_nombre:
            cursor.execute(
                "SELECT TOP 1 id FROM responsable "
                "WHERE (nombre + ' ' + apellido) LIKE %s",
                (f"%{responsable_nombre}%",))
            fila = cursor.fetchone()
            if fila:
                responsable_id = fila[0]
        if responsable_id is None:
            cursor.execute(
                "SELECT TOP 1 id FROM responsable "
                "WHERE tipo = 'tecnico' AND activo = 1 ORDER BY id")
            fila = cursor.fetchone()
            responsable_id = fila[0] if fila else 1

        # 3) Generar equipo_id PC-XXXX (puente con Mongo)
        nuevo_id = _proximo_equipo_id(conn)

        # 4) INSERT en SQL (ubicacion + propietario)
        cursor.execute(
            """
            INSERT INTO equipo
                (equipo_id, numero_serie, numero_banco, ubicacion_id,
                 responsable_id, estado, fecha_alta,
                 fecha_proximo_mantenimiento)
            VALUES (%s, %s, %s, %s, %s, 'activo', %s, NULL)
            """,
            (nuevo_id, numero_serie, int(numero_banco), int(aula_id),
             responsable_id, date.today().isoformat()))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"[ERROR SQL] No se pudo insertar el equipo: {e}")
        flash(f'Error al registrar en SQL: {e}', 'danger')
        conn.close()
        return redirect(url_for('nuevo_equipo'))
    finally:
        if conn:
            conn.close()

    # 5) INSERT del hardware en Mongo (mismo equipo_id)
    coleccion = get_mongo_collection()
    if coleccion is not None and nuevo_id:
        try:
            doc = {
                'equipo_id': nuevo_id,
                'tipo': tipo,
                'fabricante': request.form.get('fabricante', '').strip(),
                'modelo': request.form.get('modelo', '').strip(),
                'cpu': request.form.get('cpu', '').strip(),
                'ram_gb': int(request.form.get('ram_gb', 0) or 0),
                'disco_gb': int(request.form.get('disco_gb', 0) or 0),
                'disco_tipo': request.form.get('disco_tipo', 'ssd').strip(),
                'so': request.form.get('so', '').strip(),
                'monitor': request.form.get('monitor', '').strip(),
                'mouse': request.form.get('mouse') == 'on',
                'teclado': request.form.get('teclado') == 'on',
            }
            coleccion.insert_one(doc)
        except Exception as e:
            print(f"[ERROR MONGO] No se pudo insertar hardware: {e}")
            flash('Equipo creado en SQL, pero fallo el hardware en Mongo.',
                  'warning')
            return redirect(url_for('inventario'))

    flash(f'Equipo {nuevo_id} ({numero_serie}) registrado', 'success')
    return redirect(url_for('inventario'))


@app.route('/equipo/<equipo_id>/eliminar', methods=['POST'])
def eliminar_equipo(equipo_id):
    if not session.get('username'):
        return redirect(url_for('login'))

    # DELETE en SQL (ubicacion) + Mongo (hardware)
    conn = get_sql_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM equipo WHERE equipo_id = %s",
                           (equipo_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"[ERROR SQL] No se pudo eliminar {equipo_id}: {e}")
            flash('No se pudo eliminar el equipo (puede tener '
                  'mantenimientos o asignaciones asociadas).', 'danger')
            conn.close()
            return redirect(url_for('inventario'))
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
    """Diagnostico: dice si la app llega a cada servicio."""
    estado = {
        'sql': get_sql_connection() is not None,
        'mongo': get_mongo_collection() is not None,
    }
    codigo = 200 if all(estado.values()) else 503
    return jsonify(estado), codigo


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
