import serial
import schedule
import time
import json
import forecastio
import sys
from flask import Flask
from threading import Thread
from influxdb import InfluxDBClient

try:
    from flask.ext.cors import CORS  # The typical way to import flask-cors
except ImportError:
    # Path hack allows examples to be run without installation.
    import os

    parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.sys.path.insert(0, parentdir)
    from flask.ext.cors import CORS

with open('config.json') as data_file:    
    data = json.load(data_file)	
	
# COM_PORT = 2
COM_PORT = data['config']['arduino']['com_port']
BAUDRATE = data['config']['arduino']['baudrate']
READ_SENSORS_TIMER = data['config']['arduino']['read_sensors_timer']
READ_SENSORS_FAST_TIMER = data['config']['arduino']['read_sensors_fast_timer']
GET_METEO_TIMER = data['config']['arduino']['get_meteo_timer']

# DB_HOST = '192.168.1.73'
DB_HOST = data['config']['db']['host']
DB_PORT = data['config']['db']['port']
DB_NAME = data['config']['db']['name']
DB_PASS = data['config']['db']['password']
DB_USER = data['config']['db']['username']

FORECAST_API_KEY = data['config']['forecast']['api']
FORECAST_LAT = data['config']['forecast']['lat']
FORECAST_LNG = data['config']['forecast']['long']
FORECAST_LOCAL = data['config']['forecast']['local']
# FORECAST_UNIT = "si"

current_forecast = {}

influxdb = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME)

ser = serial.Serial(COM_PORT, BAUDRATE)

app = Flask(__name__, static_url_path='/static')
app.debug = True
cors = CORS(app)


def get_sensors():
    slow = get_sensors.counter == (
        (READ_SENSORS_TIMER / READ_SENSORS_FAST_TIMER) - 1)

    if slow:
        ser.write('r')
        get_sensors.counter = 0
    else:
        ser.write('x')

    get_sensors.counter += 1
    json_info = ser.readline()
    json_info = json_info.replace('\n', '')
    json_info = json_info.replace('\r', '')
    json_info = json_info.replace('\'', '\"')
    m = json.loads(json_info)
    if slow:
        m.append(current_forecast)
    try:
        influxdb.write_points(m)
    except:
        print "Unexpected error InfluxDB:", sys.exc_info()[0]


get_sensors.counter = 0


def get_meteo():
    try:
        forecast = forecastio.load_forecast(
            FORECAST_API_KEY, FORECAST_LAT, FORECAST_LNG)
        temp = forecast.currently().temperature
        humi = forecast.currently().humidity * 100
    except:
        print "Unexpected error Forecast.io:", sys.exc_info()[0]
    else:
        global current_forecast
        current_forecast = {
            "points": [[temp, humi]],
            "name": "forecastio",
            "columns": ["temperature", "humidity"]
        }


def run_schedule():
    while 1:
        schedule.run_pending()
        time.sleep(1)


@app.route('/', methods=['GET'])
def index():
    return app.send_static_file('index.html')


@app.route('/<path:path>')
def static_proxy(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(path)


if __name__ == '__main__':
    get_meteo()  # init current_forecast
    schedule.every(READ_SENSORS_FAST_TIMER).seconds.do(get_sensors)
    schedule.every(GET_METEO_TIMER).seconds.do(get_meteo)
    t = Thread(target=run_schedule)
    t.daemon = True
    t.start()
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=8080)
    ser.close()
