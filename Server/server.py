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

# COM_PORT = 2
COM_PORT = "/dev/ttyUSB0"
BAUDRATE = 9600
READ_SENSORS_TIMER = 30
READ_SENSORS_FAST_TIMER = 5
GET_METEO_TIMER = 2 * 60
# DB_HOST = '192.168.1.73'
DB_HOST = "localhost"
DB_PORT = 8086
DB_NAME = 'awarehouse'
DB_PASS = 'admin'
DB_USER = 'admin'

FORECAST_API_KEY = "111fece1a5a2d1828fb6e795221e2c25"
FORECAST_LAT = 41.1492
FORECAST_LNG = -8.6104
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
