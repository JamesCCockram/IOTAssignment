#
#  server.py
#  GroupAssignment
#
#  Created by James Cockram on 5/18/23
#

from flask import render_template, request, flash, jsonify
from flask import Flask
import paho.mqtt.publish as publish
import serial
import json
import time
import plotly.graph_objs as go
import boto3
import threading
import pandas as pd
import plotly.express as px
from datetime import datetime, time
import time as t

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
        temp_values.append(item['temperature'])
        humid_values.append(item['humidity'])


    try:
        # Create a Plotly line chart of the humidity data
        sorted_data = sorted(zip(aq_date_times, temp_values, humid_values), key=lambda x: x[0])
        # Unzip the sorted data
        sorted_aq_date_times, sorted_temp_values, sorted_humid_values = zip(*sorted_data)
    except:
        sorted_aq_date_times, sorted_temp_values, sorted_humid_values = [[],[],[]]

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
    motion_values_day = 0
    motion_values_night = 0

    def is_daytime(timestamp):
        dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
        current_time = dt.time()
        # Define daytime boundaries (adjust as needed)
        start_time = time(6, 0, 0)  # Start of daytime (6:00 AM)
        end_time = time(18, 0, 0)  # End of daytime (6:00 PM)

        # Check if the current time is within the daytime range
        if start_time <= current_time <= end_time:
            return True
        else:
            return False


    for item in items:
        motion_date_times.append(item['timeStamp'])
        motion_values.append(item['motion'])
        if is_daytime(item["timeStamp"]):
            motion_values_day += 1;
        else:
            motion_values_night += 1;


    # Create a Plotly line chart of the temperature data
    temp_chart = go.Figure()
    temp_chart.add_trace(go.Scatter(x=aq_date_times, y=sorted_temp_values, mode='lines'))
    temp_chart.update_layout(title='Temperature over Time', xaxis_title='Date/Time', yaxis_title='Temperature (°C)')
    temp_chart.write_html('static/charts/temperature_chart.html')
    

    humid_chart = go.Figure()
    humid_chart.add_trace(go.Scatter(x=sorted_aq_date_times, y=sorted_humid_values, mode='lines'))
    humid_chart.update_layout(title='Humidity over Time', xaxis_title='Date/Time', yaxis_title='Humidity %')
    humid_chart.write_html('static/charts/humidity_chart.html')
    # Create a Plotly line chart of the light data
    light_chart = go.Figure()
    light_chart.add_trace(go.Scatter(x=light_date_times, y=light_values, mode='lines'))
    light_chart.update_layout(title='Light Values over Time', xaxis_title='Date/Time', yaxis_title='Light Value')
    light_chart.write_html('static/charts/light_chart.html')

    #Create Pie Chart
    labels = ['Day', 'Night']
    values = [motion_values_day, motion_values_night]
    
    pie_chart = go.Pie(labels=labels, values=values)
    # Define the layout
    layout = go.Layout(title='Alarm System Triggers: Day vs Night')

    # Create a Figure object
    motion_chart = go.Figure(data=[pie_chart], layout=layout)
    
    motion_chart.write_html('static/charts/motion_chart.html')
 
    
    return render_template('index.html')

@app.route('/aqSensor')
def aqSensor():
    serial.close()
    serial.open()
    serial.write(b"fanDetails")
    t.sleep(1)
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
        t.sleep(2)
        serial.write(str(fanTriggerValue).encode('ascii'))
        t.sleep(2)
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
    return render_template('data.html')
   
@app.route('/filter', methods=['POST'])
def filter():
    table_name = request.json['table_name']
    print(table_name)

    table = dynamodb.Table(table_name)
    response = table.scan()
    items = response['Items']

    # Render the table data dynamically based on the selected table
    if table_name == 'light_table':
        table_html = render_template('light_table.html', items=items)
    elif table_name == 'alarm_table':
        table_html = render_template('motion_table.html', items=items)
    elif table_name == 'air_table':
        table_html = render_template('temp_table.html', items=items)
    else:
        # Handle invalid table name here
        return jsonify({'error': 'Invalid table name'})

    return jsonify({'table_html': table_html})
    
if __name__ == '__main__':
    #Start Flask Server
    app.run(debug=True)
