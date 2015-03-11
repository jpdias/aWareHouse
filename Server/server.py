import serial
import schedule
import time
import json
from flask import Flask, request, jsonify, send_from_directory
from threading import Thread
from influxdb import InfluxDBClient
from pprint import pprint

COM_PORT = 2
BAUDRATE = 9600
READ_SENSORS_TIMER = 5
DB_HOST = '192.168.1.73'
DB_PORT = 8086
DB_NAME = 'awarehouse'
DB_PASS = 'admin'
DB_USER = 'admin'

influxdb = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME)

ser = serial.Serial(COM_PORT, BAUDRATE)

app = Flask(__name__,  static_url_path='')

start_time = time.time()


def get_sensors():
  ser.write('r')
  jsonInfo = ser.readline()
  jsonInfo = jsonInfo.replace('\n', '')
  jsonInfo = jsonInfo.replace('\r', '')
  jsonInfo = jsonInfo.replace('\'', '\"')
  #o = json.dumps("[" + jsonInfo + "]")
  m = json.loads(jsonInfo)
  print(m)
  influxdb.write_points([m])


def run_schedule():
  while 1:
    schedule.run_pending()
    time.sleep(1)


@app.route('/', methods=['GET'])
def index():
  return '<html>test</html>'

if __name__ == '__main__':
  schedule.every(READ_SENSORS_TIMER).seconds.do(get_sensors)
  t = Thread(target=run_schedule)
  t.daemon = True
  t.start()
  app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)
  ser.close()
