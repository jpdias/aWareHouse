import serial
import schedule
import time
import json
import forecastio
from flask import Flask, request, jsonify, send_from_directory
from threading import Thread
from influxdb import InfluxDBClient
from pprint import pprint


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
GET_METEO_TIMER = 2 * 60
# DB_HOST = '192.168.1.73'
DB_HOST = "localhost"
DB_PORT = 8086
DB_NAME = 'awarehouse'
DB_PASS = 'admin'
DB_USER = 'admin'

FORECAST_API_KEY = 111fece1a5a2d1828fb6e795221e2c25
FORECAST_LAT = 41.1791
FORECAST_LNG = -8.5846

current_forecast = {}

forecast = forecastio.load_forecast(FORECAST_API_KEY, FORECAST_LAT, FORECAST_LNG)

influxdb = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME)

ser = serial.Serial(COM_PORT, BAUDRATE)

app = Flask(__name__, static_url_path='/static')
app.debug = True
cors = CORS(app)

def get_sensors():
  ser.write('r')
  jsonInfo = ser.readline()
  jsonInfo = jsonInfo.replace('\n', '')
  jsonInfo = jsonInfo.replace('\r', '')
  jsonInfo = jsonInfo.replace('\'', '\"')
  m = json.loads(jsonInfo)
  influxdb.write_points([m, current_forecast])

def get_meteo():
  temp = forecast.hourly().data[0].temperature
  humi = forecast.hourly().data[0].humidity
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
  get_meteo() # init current_forecast
  schedule.every(READ_SENSORS_TIMER).seconds.do(get_sensors)
  schedule.every(GET_METEO_TIMER).seconds.do(get_meteo)
  t = Thread(target=run_schedule)
  t.daemon = True
  t.start()
  app.run(debug=True, use_reloader=False, host='0.0.0.0', port=8080)
  ser.close()
