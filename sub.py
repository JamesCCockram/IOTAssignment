import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected")
    client.subscribe("/air/data")

def on_message(client, userdata, msg):
    print(msg.topic + " " + msg.payload.decode('utf-8'))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("test.mosquitto.org", 1883, 60)

client.loop_forever()
