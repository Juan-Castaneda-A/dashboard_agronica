import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client, Client
from postgrest.exceptions import APIError

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# --- Inicialización del Cliente de Supabase ---
try:
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Las variables de entorno SUPABASE_URL y SUPABASE_KEY son necesarias.")
    supabase: Client = create_client(url, key)
    print("Conexión con Supabase establecida exitosamente.")
except Exception as e:
    print(f"Error al inicializar Supabase: {e}")
    supabase = None

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "API de SOLARTRACE Live funcionando con Supabase-py!"

# --- Rutas de la API actualizadas ---

@app.route('/api/data/ingest', methods=['POST'])
def ingest_data():
    """Recibe datos del sensor y los inserta en la tabla 'sensor_readings'."""
    if not supabase:
        return jsonify({"error": "La conexión con Supabase no está configurada."}), 500

    data = request.get_json()
    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400

    try:
        # Usamos la sintaxis de supabase-py para insertar los datos
        response = supabase.table('sensor_readings').insert(data).execute()
        
        # La API de Supabase devuelve una lista de datos insertados.
        # Si la inserción fue exitosa, la respuesta tendrá datos.
        if response.data:
            return jsonify({"message": f"Datos recibidos del sensor {data.get('sensor_id', 'desconocido')}"}), 201
        else:
            # Si no hay datos, puede que haya habido un error no capturado
            return jsonify({"error": "La inserción no devolvió datos, posible error.", "details": response.error}), 400

    except APIError as e:
        return jsonify({"error": "Error de la API de Supabase", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Ocurrió un error inesperado", "details": str(e)}), 500

@app.route('/api/data/current', methods=['GET'])
def get_current_data():
    """
    Obtiene la última lectura de cada sensor llamando a la función RPC
    que creamos en la base de datos.
    """
    if not supabase:
        return jsonify({"error": "La conexión con Supabase no está configurada."}), 500

    try:
        # Llamamos a la función 'get_latest_readings' que creamos en el SQL Editor
        response = supabase.rpc('get_latest_readings', {}).execute()

        if response.data:
            # Formateamos la respuesta para que sea un diccionario {sensor_id: datos}
            formatted_data = {row['sensor_id']: row for row in response.data}
            return jsonify(formatted_data)
        else:
            return jsonify({"error": "No se encontraron datos", "details": response.error}), 404

    except APIError as e:
        return jsonify({"error": "Error de la API de Supabase", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Ocurrió un error inesperado", "details": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)

