import serial
import schedule
import time
from flask import Flask, request
from threading import Thread

COM_PORT = 2
BAUDRATE = 9600

ser = serial.Serial(COM_PORT, BAUDRATE)

app = Flask(__name__)

start_time = time.time()


def run_every_10_seconds():
  print ser.name
  ser.write('r')
  json = ser.readline()
  print json


def run_schedule():
  while 1:
    schedule.run_pending()
    time.sleep(1)


@app.route('/', methods=['GET'])
def index():
  return '<html>test</html>'

if __name__ == '__main__':
  schedule.every(10).seconds.do(run_every_10_seconds)
  t = Thread(target=run_schedule)
  t.start()
  app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)
  ser.close()
