import time
import json
import logging
from threading import Thread
from datetime import datetime, timedelta
from functools import wraps

import serial
import schedule
import forecastio
import mandrill
from flask import Flask, request, jsonify
from influxdb.influxdb08 import InfluxDBClient
from twilio.rest import TwilioRestClient

try:
    from flask.ext.cors import CORS  # The typical way to import flask-cors
except ImportError:
    # Path hack allows examples to be run without installation.
    import os

    parentDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.sys.path.insert(0, parentDir)
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


class Throttle(object):
    """
    Decorator that prevents a function from being called more than once every
    time period.

    To create a function that cannot be called more than once a minute:

        @Throttle(minutes=1)
        def my_fun():
            pass
    """

    def __init__(self, seconds=0, minutes=0, hours=0):
        self.throttle_period = timedelta(
            seconds=seconds, minutes=minutes, hours=hours
        )
        self.time_of_last_call = datetime.min

    def __call__(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            now = datetime.now()
            time_since_last_call = now - self.time_of_last_call

            if time_since_last_call > self.throttle_period:
                self.time_of_last_call = now
                return fn(*args, **kwargs)

        return wrapper


def compare(op, val1, val2):
    if val1 is None or val2 is None:
        return False
    elif op == '>':
        return val1 > val2
    elif op == '>=':
        return val1 >= val2
    elif op == '<':
        return val1 < val2
    elif op == '<=':
        return val1 <= val2
    elif op == '=':
        return val1 == val2
    return False


def op_name(op):
    if op == '>':
        return 'higher'
    elif op == '>=':
        return 'higher or equal'
    elif op == '<':
        return 'lower'
    elif op == '<=':
        return 'lower or equal'
    elif op == '=':
        return 'equal'
    return None


@Throttle(minutes=1)
def do_action(action, sensor_type, op, sensor_value, warning_value):
    logging.debug(
        'Executing action {action} sensor value {sensor} and warning value {warning}'.format(action=action,
                                                                                             sensor=sensor_value,
                                                                                             warning=warning_value))
    message = \
        'Warning: {type} value {sensor} is {op} than configured warning level {warning}'.format(type=sensor_type,
                                                                                                sensor=sensor_value,
                                                                                                op=op_name(op),
                                                                                                warning=warning_value)
    if action == 'mail':
        send_mail('aWarehouse warning', message)
    elif action == 'sms':
        send_sms(message)


def check_alerts(conf, sensors):
    logging.debug('Checking alerts')
    for w in conf['warnings']:
        action = w['action']
        op = w['op']
        warning_value = w['value']
        sensor_type = w['type']
        sensor_value = get_sensor_value(sensors, sensor_type)
        logging.debug('Checking alerts action {action} {sensor} {op} {warning}'.format(action=action,
                                                                                       sensor=sensor_value,
                                                                                       op=op, warning=warning_value))
        if warning_value is None:
            continue
        if compare(op, sensor_value, warning_value):
            do_action(action, sensor_type, op, sensor_value, warning_value)


def get_sensor_value(sensors, sensor_type):
    names = {
        'temperature': ['sensors', 'temp1'],
        'humidity': ['sensors', 'humidity'],
        'brightness': ['sensors', 'light_sensor'],
        'heat': ['sensors', 'heat_index'],
        'sound': ['sensors_fast', 'sound']
    }
    for sensor in sensors:
        if sensor['name'] == names[sensor_type][0]:
            return sensor['points'][0][sensor['columns'].index(names[sensor_type][1])]
    return None


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


def send_mail(subj, msg):
    to = config['mandrill']['to']
    key = config['mandrill']['token']
    from_email = config['mandrill']['from']

    kwargs = {'api_key': key,
              'reply_to': from_email,
              'recipient': 'Recipient',
              'from_email': from_email
              }
    post_mail(to=to, msg=msg, subj=subj, **kwargs)


def post_mail(to, subj, msg, **kwargs):
    """ Sends the message by posting to Mandrill API

        @param to: the recipient for the message
        @type to: str

        @param subj: the subject for the email
        @type subj: str

        @param msg: the body of the message, in plain text
        @type msg: str

        @param kwargs: other settings, compliant with Mandrill API
        @type kwargs: dict

        @see: https://mandrillapp.com/api/docs/
    """
    msg = {
        'from_email': kwargs.get('from_email'),
        'from_name': 'aWarehouse',
        'html': '<h3>Automated Alert</h3><p>{msg}</p><h6>Sent via Mandrill API</h6>'.format(msg=msg),
        'subject': subj,
        'to': [
            {'email': to,
             'type': 'to'
             }
        ]
    }
    mc = mandrill.Mandrill(kwargs.get('api_key'))
    try:
        res = mc.messages.send(msg, async=kwargs.get('async', False))
        if res and not res[0].get('status') == 'sent':
            logging.error('Could not send email to {to}; status: {status}, reason: {reason}'
                          .format(to=to, status=res.get('status', 'unknown'),
                                  reason=res.get('reject_reason')))
            exit(1)
    except mandrill.Error, e:
        # Mandrill errors are thrown as exceptions
        logging.error('A mandrill error occurred: {} - {}'.format(e.__class__.__name__, e))
    logging.info('Message sent to {to}'.format(to=to))


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
        logging.exception('Unexpected error InfluxDB')

    check_alerts(config, m)


get_sensors.counter = 0


def get_meteo():
    try:
        forecast = forecastio.load_forecast(
            config['forecast']['api'], config['forecast']['lat'],
            config['forecast']['long'])
        temp = forecast.currently().temperature
        humi = forecast.currently().humidity * 100
    except:
        logging.exception('Unexpected error Forecast.io')
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
    logging.basicConfig(format='%(asctime)-15s [%(levelname)s] %(message)s',
                        datefmt='%Y/%m/%d %H:%M:%S',
                        level=loglevel)
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
