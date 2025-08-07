#!/usr/bin/env python3
# Simple eHMI: full-screen “CROSS” (green) or “STOP” (red) using PIL + SetImage.

import sys
import json
import time
import traceback

import paho.mqtt.client as mqtt
from PIL import Image, ImageDraw, ImageFont
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

MQTT_BROKER         = "atcll-services.nap.av.it.pt"
MQTT_PORT           = 1884
MQTT_USERNAME       = "atcll-services"
MQTT_PASSWORD       = "bWAoaB&6kQ#pjE9@Dv2opvjDiyxKsw"
MQTT_TOPIC          = "obu157/vanetza/time/cam_full"
MQTT_DEBUG_TOPIC    = "ehmi"

# — Matrix Configuration —
MATRIX_ROWS   = 64
MATRIX_CHAIN  = 2
MATRIX_PAR    = 1
BRIGHTNESS    = 100

# Initialize RGBMatrix
options = RGBMatrixOptions()
options.rows            = MATRIX_ROWS
options.chain_length    = MATRIX_CHAIN
options.parallel        = MATRIX_PAR
options.brightness      = BRIGHTNESS
options.hardware_mapping= 'regular'
options.gpio_slowdown   = 4             # Remove Flicker because RPi4 is too fast

matrix = RGBMatrix(options=options)
font = graphics.Font()
font.LoadFont("../../../fonts/myfont-p17.bdf")

MODES = {
    "go": graphics.Color(0, 220, 0),
    "cross": graphics.Color(0, 220, 0),
    "stop":  graphics.Color(220, 0, 0),
}

def render_frame(mode_text):
    mode = mode_text.lower()
    bg_color = MODES.get(mode, graphics.Color(0, 0, 0))   # always a Color
    fg_color = graphics.Color(255, 255, 255)              # white text

    off = matrix.CreateFrameCanvas()

    # 1) Fill background by drawing full-width horizontal lines
    for y in range(matrix.height):
        graphics.DrawLine(off, 0, y, matrix.width - 1, y, bg_color)

    # 2) Measure text width (returns pixels) using DrawText at (0,0)
    text = mode.upper()
    text_width = graphics.DrawText(off, font, 0, 0, fg_color, text)

    # 3) Compute centered position
    x = (matrix.width  - text_width) // 2
    y = (matrix.height + 17) // 2

    # 4) Draw text at the centered coords
    graphics.DrawText(off, font, x, y, fg_color, text)

    # 5) Swap to display it
    off = matrix.SwapOnVSync(off)

def render_initial_frame():
    image = Image.open("./nap.png")
    image.thumbnail((matrix.width, matrix.height), Image.ANTIALIAS)
    matrix.SetImage(image.convert('RGB'))

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker.")
        client.subscribe(MQTT_TOPIC)
        client.subscribe(MQTT_DEBUG_TOPIC)
        print(f"Subscribed to topics: {MQTT_TOPIC}, {MQTT_DEBUG_TOPIC}")
    else:
        print(f"MQTT connection failed with code {rc}")

def on_message(client, userdata, msg):
    if msg.topic == MQTT_TOPIC:
        try:
            data   = json.loads(msg.payload.decode("utf-8"))
            speed  = (data["fields"]["cam"]
                        ["camParameters"]["highFrequencyContainer"]
                        ["basicVehicleContainerHighFrequency"]["speed"]["speedValue"])
            
            if speed > 0:
                render_frame("stop")
            else:
                render_frame("cross")
            print(f"Received speed: {speed}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Failed to parse JSON or find key: {e}")
    elif msg.topic == MQTT_DEBUG_TOPIC:
        state = msg.payload.decode().strip().lower()
        print(f"Received: {state}")

        if state == "reset":
            render_initial_frame()
        else:
            render_frame(state)

def main():
    render_initial_frame()

    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    # render_frame("stop")  # initial state

    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            client.loop_forever()
        except Exception as e:
            print("MQTT crashed:", e)
            traceback.print_exc()
            time.sleep(5)

if __name__ == "__main__":
    main()
