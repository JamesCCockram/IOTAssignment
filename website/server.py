from flask import render_template, request, flash
from flask import Flask
import paho.mqtt.publish as publish
import serial
import json
import time as t
import plotly.graph_objs as go
import boto3

app = Flask(__name__)

#Setup Serial Communication with Device
DEVICE = '/dev/tty.usbmodem212401'
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
    co2_date_times = ["2/3/2023", "3/3/2023", "4/3/2023"]
    co2_values = [500, 400, 700]
    tvoc_date_times = ["2/3/2023", "3/3/2023", "4/3/2023"]
    tvoc_values = [500, 400, 700]
    light_values = [700, 400, 600]
        # Create a Plotly line chart of the co2 data
    co2_chart = go.Figure()
    co2_chart.add_trace(go.Scatter(x=co2_date_times, y=co2_values, mode='lines'))
    co2_chart.update_layout(title='CO2 Values over Time', xaxis_title='Date/Time', yaxis_title='CO2 Value (ppm)')
    co2_chart.write_html('static/co2_chart.html')

    # Create a Plotly line chart of the tvoc data
    tvoc_chart = go.Figure()
    tvoc_chart.add_trace(go.Scatter(x=tvoc_date_times, y=tvoc_values, mode='lines'))
    tvoc_chart.update_layout(title='TVOC Values over Time', xaxis_title='Date/Time', yaxis_title='TVOC Value (ppb)')
    tvoc_chart.write_html('static/tvoc_chart.html')
    
    # Create a Plotly line chart of the light data
    tvoc_chart = go.Figure()
    tvoc_chart.add_trace(go.Scatter(x=tvoc_date_times, y=light_values, mode='lines'))
    tvoc_chart.update_layout(title='Light Values over Time', xaxis_title='Date/Time', yaxis_title='Light Value')
    tvoc_chart.write_html('static/light_chart.html')
    
    return render_template('index.html')

@app.route('/aqSensor')
def aqSensor():
    serial.close()
    serial.open()
    serial.write(b"buzzerDetails")
    t.sleep(1)
    data = serial.readline().decode('utf-8')
    j = json.loads(data)

    buzzerStatus = j["buzzerEnabled"]
    if buzzerStatus == False:
        currentBuzzerStatus = "Disabled"
    else:
        currentBuzzerStatus = "Enabled"
    return render_template('aqSensor.html', currentBuzzerTrigger = j["buzzerTriggerValue"], currentBuzzerStatus = currentBuzzerStatus)

@app.route('/success', methods = ["GET", "POST"])
def success():
    if request.method == "POST":
        buzzerStatus = request.form.get("buzzer")
        buzzerTriggerValue = request.form.get("triggerValue")
        serial.write(b"changeBuzzer")
        t.sleep(2)
        serial.write(str(buzzerTriggerValue).encode('ascii'))
        t.sleep(2)
        serial.close()
        serial.open()
        if(buzzerStatus == "True"):
            serial.write(b"enableBuzzer")
        else:
            serial.write(b"disableBuzzer")
    return render_template('success.html')

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
        return render_template('data.html', items = items)
   except Exception as e:
        return f"Error occurred: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
