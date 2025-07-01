import eventlet
eventlet.monkey_patch()

import json
import traceback
from flask import Flask, render_template
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt

# --- Configuration -----------------------------------------------------------
MQTT_BROKER   = "atcll-services.nap.av.it.pt"
MQTT_PORT     = 1884
MQTT_USERNAME = "atcll-services"
MQTT_PASSWORD = "bWAoaB&6kQ#pjE9@Dv2opvjDiyxKsw"
MQTT_TOPIC    = "obu157/vanetza/time/cam_full"

# --- App initialisation ------------------------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = "secret-key"          # change in production
socketio = SocketIO(app, async_mode="eventlet")  # must match Gunicorn worker

# --- Vehicle state -----------------------------------------------------------
vehicle_state = {"speed": 1}

# --- MQTT client -------------------------------------------------------------
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Successfully connected to MQTT broker.")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect to MQTT broker, return code {rc}")

def on_message(client, userdata, msg):
    global vehicle_state
    try:
        data   = json.loads(msg.payload.decode("utf-8"))
        speed  = (data["fields"]["cam"]
                      ["camParameters"]["highFrequencyContainer"]
                      ["basicVehicleContainerHighFrequency"]["speed"]["speedValue"])
        vehicle_state["speed"] = speed
        socketio.emit("status_update", {"speed": speed})
        print(f"Received speed: {speed} -> Pushed to clients")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Failed to parse JSON or find key: {e}")

def mqtt_background_thread():
    print("Initializing MQTT client for background thread.")
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    while True:                              # auto-reconnect loop
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            client.loop_forever()            # blocks until connection drops
        except Exception as e:
            print("MQTT thread crashed:", e)
            traceback.print_exc()            # full stack trace
            print("Re-trying in 5 s …")
            eventlet.sleep(5)                # don’t burn CPU in a tight loop

# --- Flask routes ------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

# --- Socket.IO events --------------------------------------------------------
@socketio.on("connect")
def handle_connect():
    print("Web client connected")
    socketio.emit("status_update", {"speed": vehicle_state["speed"]})

# --- Start background MQTT worker as soon as the module is imported ----------
socketio.start_background_task(target=mqtt_background_thread)

if __name__ == "__main__":
    print("Starting server in debug mode …")
    socketio.run(app, host="0.0.0.0", port=5003, debug=True)
