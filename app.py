import os
import json
import psycopg2
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from datetime import datetime

# Cargar variables de entorno del archivo .env
load_dotenv()
app = Flask(__name__)

# --- CONFIGURACIÓN DE LA BASE DE DATOS (Supabase/PostgreSQL) ---
# Usamos la URL completa de la DB
#DATABASE_URL = os.getenv("SUPABASE_DB_URL")
# --- CONFIGURACIÓN DE LA BASE DE DATOS (Supabase/PostgreSQL) ---
# En lugar de una URL, cargamos los componentes individuales
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

def get_db_connection():
    """Establece y devuelve una conexión a la base de datos Supabase."""
    
    # Debug detallado de cada variable
    variables = [
        ("DB_HOST", DB_HOST),
        ("DB_NAME", DB_NAME), 
        ("DB_USER", DB_USER),
        ("DB_PASSWORD", DB_PASSWORD),
        ("DB_PORT", DB_PORT)
    ]
    
    for name, value in variables:
        try:
            # Intentar codificar en UTF-8
            value.encode('utf-8')
            print(f"✅ {name} es UTF-8 valido: {value}")
        except UnicodeEncodeError as e:
            print(f"❌ {name} NO es UTF-8 valido: {value}")
            print(f"   Error: {e}")
            # Mostrar representación hexadecimal del problema
            hex_repr = ' '.join([f'{byte:02x}' for byte in value.encode('latin1')])
            print(f"   Hexadecimal: {hex_repr}")
    
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        print("✅ Conexión a la base de datos establecida correctamente")
        return conn
    except UnicodeDecodeError as e:
        print(f"❌ Error de Unicode específico: {e}")
        print("💡 Intentando con Latin-1...")
        # Intentar con Latin-1 como fallback
        try:
            conn = psycopg2.connect(
                host=DB_HOST.encode('latin1').decode('latin1'),
                database=DB_NAME.encode('latin1').decode('latin1'),
                user=DB_USER.encode('latin1').decode('latin1'),
                password=DB_PASSWORD.encode('latin1').decode('latin1'),
                port=DB_PORT
            )
            print("✅ Conexión exitosa con Latin-1")
            return conn
        except Exception as e2:
            print(f"❌ Fallback Latin-1 también falló: {e2}")
            raise
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        raise
# ... (El resto del código de app.py sigue igual) ...

# def get_db_connection():
#     """Establece y devuelve una conexión a la base de datos Supabase."""
#     conn = psycopg2.connect(DATABASE_URL)
#     return conn

# --- 1. RUTA DE INGESTA (POST): Para recibir datos del ESP32 ---
# (Simulada por ahora, pero lista para el hardware)
@app.route('/api/data/ingest', methods=['POST'])
def ingest_data():
    """Recibe datos JSON de un sensor y los inserta en Supabase."""
    
    try:
        # 1. Validación y Extracción de datos
        data = request.get_json()
        if not data or 'sensor_id' not in data:
            return jsonify({"message": "Faltan datos o sensor_id."}), 400

        sensor_id = data.get('sensor_id')
        print(f"📥 Recibiendo datos del sensor: {sensor_id}")
        
        # Prepara la lista de valores espectrales
        channel_data = (
            data.get('ch_415'), data.get('ch_440'), data.get('ch_485'),
            data.get('ch_515'), data.get('ch_555'), data.get('ch_590'),
            data.get('ch_610'), data.get('ch_680'), data.get('ch_730'),
            data.get('ch_760'), data.get('ch_860'), data.get('ch_clear'),
            data.get('total_lux')
        )
        
        # 2. Conexión e Inserción en la DB
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Consulta de inserción de datos
        insert_query = """
        INSERT INTO sensor_readings (
            sensor_id, ch_415, ch_440, ch_485, ch_515, ch_555, ch_590, 
            ch_610, ch_680, ch_730, ch_760, ch_860, ch_clear, total_lux
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        
        # Combina el sensor_id con los datos de los canales
        insert_values = (sensor_id,) + channel_data
        
        cur.execute(insert_query, insert_values)
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Datos de {sensor_id} guardados correctamente")
        return jsonify({"message": f"Datos de {sensor_id} recibidos y guardados correctamente."}), 201

    except psycopg2.Error as e:
        print(f"❌ Error de base de datos: {e}")
        return jsonify({"message": f"Error al guardar los datos en la base de datos: {str(e)}"}), 500
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return jsonify({"message": f"Error interno del servidor: {str(e)}"}), 500

# --- 2. RUTA DE CONSULTA (GET): Para el Dashboard Web ---
@app.route('/api/data/current', methods=['GET'])
def get_current_data():
    """Consulta y devuelve las últimas lecturas de cada uno de los 3 sensores."""
    
    # IDs de los 3 sensores
    sensor_ids = ['Referencia', 'Cama_1', 'Cama_2']
    latest_readings = []
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        for sensor_id in sensor_ids:
            # Consulta para obtener el último registro de un sensor específico
            query = """
            SELECT * FROM sensor_readings
            WHERE sensor_id = %s
            ORDER BY timestamp DESC
            LIMIT 1;
            """
            cur.execute(query, (sensor_id,))
            record = cur.fetchone()
            
            if record:
                # Obtener los nombres de las columnas para crear un diccionario (JSON)
                column_names = [desc[0] for desc in cur.description]
                reading = dict(zip(column_names, record))
                latest_readings.append(reading)

        cur.close()
        conn.close()
        
        # Si no hay datos, devuelve un mensaje vacío pero no falla
        if not latest_readings:
            return jsonify({"message": "No hay datos de sensores disponibles.", "data": []}), 200

        # Devuelve un arreglo con los últimos datos de los 3 sensores
        return jsonify({"data": latest_readings}), 200

    except psycopg2.Error as e:
        print(f"Error de base de datos: {e}")
        return jsonify({"message": "Error al obtener datos de la base de datos."}), 500

# --- Ejecución del servidor ---
if __name__ == '__main__':
    # Ejecutar en modo debug para desarrollo
    app.run(debug=True, host='0.0.0.0', port=5000)