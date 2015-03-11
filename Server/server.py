import serial
import schedule
import time
from flask import Flask, request
from threading import Thread
from influxdb import InfluxDBClient

COM_PORT = 2
BAUDRATE = 9600
READ_THREAD = 10
DB_HOST = 'localhost'
DB_HOST_PORT = 8086
DB_NAME = 'awarehouse'
DB_PASS = 'admin'
DB_USER = 'admin'

influxdb = InfluxDBClient(DB_HOST, DB_HOST_PORT, DB_USER, DB_PASS, DB_NAME)

ser = serial.Serial(COM_PORT, BAUDRATE)

app = Flask(__name__)

start_time = time.time()


def get_sensors():
  ser.write('r')
  json = ser.readline()
  influxdb.write_points([json])
  print json


def run_schedule():
  while 1:
    schedule.run_pending()
    time.sleep(1)


@app.route('/', methods=['GET'])
def index():
  return '<html>test</html>'

if __name__ == '__main__':
  schedule.every(READ_THREAD).seconds.do(get_sensors)
  t = Thread(target=run_schedule)
  t.start()
  app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)
  ser.close()
