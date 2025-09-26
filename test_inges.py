import requests
import random
import time

# URL de tu API de ingesta
API_URL = "http://127.0.0.1:5000/api/data/ingest"
SENSOR_IDS = ['Referencia', 'Cama_1', 'Cama_2']

def generate_mock_data(sensor_id):
    """Genera un diccionario de datos ficticios del sensor AS734X."""
    
    # Genera valores base aleatorios para simular variaciones
    base_lux = random.randint(1000, 5000) 
    
    # Simula un perfil de luz variable según el sensor (Cama 1 vs Cama 2)
    # Ejemplo: si es Cama_1, tiene más luz, si es Cama_2, tiene un poco menos
    factor = 1.0
    if sensor_id == 'Cama_1':
        factor = 1.05  # Ligeramente más luz en Cama 1
    elif sensor_id == 'Cama_2':
        factor = 0.95  # Ligeramente menos luz en Cama 2

    # El AS734X tiene 11 bandas de color + Clear (blanca)
    data = {
        "sensor_id": sensor_id,
        "ch_415": int(base_lux * 0.1 * factor),  # Violeta
        "ch_440": int(base_lux * 0.2 * factor),  # Azul
        "ch_485": int(base_lux * 0.3 * factor),  # Cian
        "ch_515": int(base_lux * 0.4 * factor),  # Verde
        "ch_555": int(base_lux * 0.45 * factor), # Verde-Amarillo
        "ch_590": int(base_lux * 0.35 * factor), # Naranja
        "ch_610": int(base_lux * 0.5 * factor),  # Rojo (Importante para plantas)
        "ch_680": int(base_lux * 0.48 * factor), # Rojo lejano
        "ch_730": int(base_lux * 0.1 * factor),
        "ch_760": int(base_lux * 0.05 * factor),
        "ch_860": int(base_lux * 0.03 * factor), # Infrarrojo
        "ch_clear": int(base_lux * 0.8 * factor), # Canal de luz clara
        "total_lux": int(base_lux * factor * 0.95) # Intensidad total estimada
    }
    return data

def run_simulation():
    """Envía datos de los 3 sensores a la API, simulando el envío real."""
    print("--- Iniciando Simulación de Sensores ---")
    while True:
        for sensor_id in SENSOR_IDS:
            data = generate_mock_data(sensor_id)
            try:
                response = requests.post(API_URL, json=data)
                
                if response.status_code == 201:
                    print(f"✅ Éxito: {sensor_id} - Lux: {data['total_lux']}")
                else:
                    # **¡Añadimos manejo de errores más robusto aquí!**
                    try:
                        # Intenta leer el JSON si el servidor lo envió
                        error_message = response.json().get('message', 'Mensaje de error no disponible.')
                    except requests.exceptions.JSONDecodeError:
                        # Si no es JSON (ej. HTML de error 500), mostramos el código de estado
                        error_message = f"Respuesta no-JSON. Estado: {response.status_code}"
                        
                    print(f"❌ Error al enviar {sensor_id}: {error_message}")
            except requests.exceptions.ConnectionError:
                print("⚠️ Error de conexión. Asegúrate de que Flask esté corriendo.")
                return

        time.sleep(5)

if __name__ == '__main__':
    run_simulation()