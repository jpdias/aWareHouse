import serial
import schedule
import time
import json
import forecastio
import sys
import logging
from flask import Flask, request, jsonify
from threading import Thread
from influxdb import InfluxDBClient
from twilio.rest import TwilioRestClient
from decimal import Decimal

try:
    from flask.ext.cors import CORS  # The typical way to import flask-cors
except ImportError:
    # Path hack allows examples to be run without installation.
    import os

    parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.sys.path.insert(0, parentdir)
    from flask.ext.cors import CORS

FILE_NAME = "config.json"
config = {}
current_forecast = {}
client = None
influxdb = None
ser = None

app = Flask(__name__, static_url_path='/static')
app.debug = True
cors = CORS(app)


def load_file():
    with open(FILE_NAME, "r") as data_file:
        global config
        config = json.load(data_file)
        global client
        client = TwilioRestClient(
            config['twilio']['sid'], config['twilio']['token'])
        global influxdb
        influxdb = InfluxDBClient(config['db']['host'],
                                  config['db']['port'], config['db']['username'],
                                  config['db']['password'], config['db']['name'])
        global ser
        ser = serial.Serial(config['arduino']['com_port'], config['arduino']['baudrate'])
        data_file.close()


def send_sms(content):
    client.messages.create(
        to=config['twilio']['to'],
        from_=config['twilio']['from'],
        body=content,
    )


def get_sensors():
    slow = get_sensors.counter == (
        (
            config['arduino']['read_sensors_timer'] / config['arduino']['read_sensors_fast_timer']) - 1)
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
        print "Unexpected error InfluxDB:", sys.exc_info()

get_sensors.counter = 0


def get_meteo():
    try:
        forecast = forecastio.load_forecast(
            config['forecast']['api'], config['forecast']['lat'],
            config['forecast']['long'])
        temp = forecast.currently().temperature
        humi = forecast.currently().humidity * 100
    except:
        print "Unexpected error Forecast.io:", sys.exc_info()
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


@app.route('/api/config', methods=['GET', 'POST'])
def get_api_config():
    if request.method == 'GET':
        return jsonify(config)
    else:
        data = request.json
        with open(FILE_NAME, 'w') as outfile:
            json.dump(data, outfile, indent=4)
        load_file()
        return "done"


@app.route('/config', methods=['GET'])
def configuration():
    return app.send_static_file('configuration/index.html')


@app.route('/<path:path>')
def static_proxy(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(path)


if __name__ == '__main__':
    loglevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)-15s [%(levelname)s] %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=loglevel)
    logging.info('aWarehouse starting...')
    load_file()
    get_meteo()  # init current_forecast
    schedule.every(
        config['arduino']['read_sensors_fast_timer']).seconds.do(get_sensors)
    schedule.every(
        config['arduino']['get_meteo_timer']).seconds.do(get_meteo)
    t = Thread(target=run_schedule)
    t.daemon = True
    t.start()
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=8080)
    ser.close()
