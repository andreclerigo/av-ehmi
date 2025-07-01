import json
import threading
import time
from flask import Flask, render_template
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt

# --- Configuration ---
MQTT_BROKER = "atcll-services.nap.av.it.pt"
MQTT_PORT = 1884
MQTT_USERNAME = "atcll-services"
MQTT_PASSWORD = "bWAoaB&6kQ#pjE9@Dv2opvjDiyxKsw"
MQTT_TOPIC = "obu157/vanetza/time/cam_full"

# --- App Initialization ---
app = Flask(__name__)
# In a production environment, you'd want a more secure secret key
app.config['SECRET_KEY'] = 'secret!'
# Use async_mode='threading' to work well with the Paho MQTT client's blocking loop
socketio = SocketIO(app, async_mode='threading')

# --- Vehicle State ---
# This will hold the latest speed. No lock needed for this simple case as updates
# are managed in a single MQTT thread and read by SocketIO events.
vehicle_state = {"speed": 0}

# --- MQTT Client Setup ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Successfully connected to MQTT broker.")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    global vehicle_state
    try:
        data = json.loads(msg.payload.decode('utf-8'))
        speed = data["fields"]["cam"]["camParameters"]["highFrequencyContainer"]["basicVehicleContainerHighFrequency"]["speed"]["speedValue"]
        vehicle_state["speed"] = speed
        
        # A new message has arrived, so push it to all connected clients instantly.
        socketio.emit('status_update', {'speed': speed})
        
        print(f"Received speed: {speed} -> Pushed to clients")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Failed to parse JSON or find key: {e}")

def mqtt_thread_target():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

# --- Flask Routes ---
@app.route('/')
def index():
    """Serve the main eHMI page."""
    return render_template('index.html')

# --- SocketIO Events ---
@socketio.on('connect')
def handle_connect():
    """A client connected. Send them the current status immediately."""
    print("Client connected")
    # Send the last known status to the newly connected client
    socketio.emit('status_update', {'speed': vehicle_state['speed']})

# --- Main Execution ---
if __name__ == '__main__':
    # Start the MQTT client in a separate thread
    mqtt_thread = threading.Thread(target=mqtt_thread_target, daemon=True)
    mqtt_thread.start()

    # Run the Flask-SocketIO web server
    print("Starting Flask-SocketIO server...")
    socketio.run(app, host='0.0.0.0', port=5003)
