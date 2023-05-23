import paho.mqtt.publish as publish
import serial
import time as t
import json

#MQTT
HOST = "test.mosquitto.org"
TOPIC = "/air/data"

#SERIAL
DEVICE = '/dev/tty.usbmodem12401'
serial = serial.Serial(DEVICE, 9600, timeout=1)
t.sleep(10)


while True:
    serial.write(b"getData")
    t.sleep(5)
        #Read the recieved line and decode it
    try:
      data = serial.readline().decode('utf-8')
          #Use Python's JSON library to read the JSON data
      j = json.loads(data)

      data = {"temperature" : j["temp"], "humidity" : j["humid"]}

      publish.single(TOPIC, payload=json.dumps(data), hostname=HOST)
      print("Published: '" + json.dumps(data) + "' to the topic: " + TOPIC)
    except:
       print("Arduino Busy")
    t.sleep(5)