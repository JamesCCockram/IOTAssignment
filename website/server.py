from flask import render_template, request, flash
from flask import Flask
import paho.mqtt.publish as publish
import serial
import json
import time
import plotly.graph_objs as go
import boto3
import threading

app = Flask(__name__)

#Setup Serial Communication with Device
DEVICE = '/dev/tty.usbmodem12401'
serial = serial.Serial(DEVICE, 9600, timeout=1)

#MQTT
HOST = "test.mosquitto.org"
TOPIC = "/lightSensor/data"

#AWS
dynamodb = boto3.resource('dynamodb')
table_name = 'air_table'  # Specify your DynamoDB table name
table = dynamodb.Table(table_name)

@app.route('/')
def index():
    table = dynamodb.Table('air_table')
    response = table.scan()
    items = response['Items']
    #Setup arrays for the graphs
    aq_date_times = []
    temp_values = []
    humid_values = []
    for item in items:
        aq_date_times.append(item['timeStamp'])
        temp_values.append(item['co2'])
        humid_values.append(item['tvoc'])

    table = dynamodb.Table('light_table')
    response = table.scan()
    items = response['Items']
    light_date_times = []
    light_values = []
    for item in items:
        light_date_times.append(item['timeStamp'])
        light_values.append(item['light'])

    table = dynamodb.Table('alarm_table')
    response = table.scan()
    items = response['Items']
    motion_date_times = []
    motion_values = []
    for item in items:
        light_date_times.append(item['timeStamp'])
        light_values.append(item['Motion'])


    # Create a Plotly line chart of the temperature data
    temp_chart = go.Figure()
    temp_chart.add_trace(go.Scatter(x=aq_date_times, y=temp_values, mode='lines'))
    temp_chart.update_layout(title='Temperature over Time', xaxis_title='Date/Time', yaxis_title='Temperature (°C)')
    temp_chart.write_html('static/charts/temperature_chart.html')
    
    # Create a Plotly line chart of the humidity data
    humid_chart = go.Figure()
    humid_chart.add_trace(go.Scatter(x=aq_date_times, y=humid_values, mode='lines'))
    humid_chart.update_layout(title='Humidity over Time', xaxis_title='Date/Time', yaxis_title='Humidity %')
    humid_chart.write_html('static/charts/humidity_chart.html')
    # Create a Plotly line chart of the light data
    light_chart = go.Figure()
    light_chart.add_trace(go.Scatter(x=light_date_times, y=light_values, mode='lines'))
    light_chart.update_layout(title='Light Values over Time', xaxis_title='Date/Time', yaxis_title='Light Value')
    light_chart.write_html('static/charts/light_chart.html')
    
    return render_template('index.html')

@app.route('/aqSensor')
def aqSensor():
    serial.close()
    serial.open()
    serial.write(b"fanDetails")
    time.sleep(1)
    try:
        data = serial.readline().decode('utf-8')
        j = json.loads(data)

        fanTriggerValue = j["fanTriggerValue"]
        fanStatus = j["fanOn"]
        if fanStatus == False:
            currentFanStatus = "Disabled"
        else:
            currentFanStatus = "Enabled"
    except:
        fanTriggerValue = "Error"
        currentFanStatus = "Error"

    return render_template('aqSensor.html', currentFanTrigger = fanTriggerValue, currentFanStatus = currentFanStatus)

@app.route('/aqSuccess', methods = ["GET", "POST"])
def aqSuccess():
    if request.method == "POST":
        fanStatus = request.form.get("fan")
        fanTriggerValue = request.form.get("triggerValue")
        serial.write(b"changeFan")
        time.sleep(2)
        serial.write(str(fanTriggerValue).encode('ascii'))
        time.sleep(2)
        serial.close()
        serial.open()
        if(fanStatus == "True"):
            serial.write(b"enableFan")
        else:
            serial.write(b"disableFan")
    return render_template('aqSuccess.html')

@app.route('/light')
def light():
    return render_template('light.html')

@app.route('/lightUpdate', methods=['POST'])
def lightUpdate():
    value = request.form['value']
    led_state = request.form['led_state']
    data = value + "," + led_state
    publish.single(TOPIC, payload=data, hostname=HOST)
    if led_state == "0":
        led_state_string = "off"
    else:
        led_state_string = "on"
    return render_template('lightSuccess.html', value=value, led_state=led_state_string)


@app.route('/motion')
def motion():
    return render_template('motion.html')

@app.route('/motionUpdate')
def motionUpdate():
    publish.single("/motionSensor/data", payload="off", hostname=HOST)
    return render_template('motionSuccess.html')

@app.route("/data")
def data():
   try:
        response = table.scan()
        items = response['Items']
        print(items)
        return render_template('data.html', items = items)
   except Exception as e:
        return f"Error occurred: {str(e)}"

if __name__ == '__main__':
    #Start Flask Server
    app.run(debug=True)
