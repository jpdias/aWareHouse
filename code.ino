#include <OneWire.h>
#include <DallasTemperature.h>

#define DS18B20_PIN 10
#define READ A0

OneWire oneWire(DS18B20_PIN);
DallasTemperature sensors(&oneWire);

void setup() {
  Serial.begin(9600);
  sensors.begin();
}

void loop() {

  int b = Serial.read();
  String json = "{";

  //if ((char)b == 'r') {

  json += temperature();
  json += brightness() + "}";
  Serial.println(json);

  delay(100);
  //}
}

String temperature() {
  String json;
  sensors.requestTemperatures();
  for (byte i = 0; i < sensors.getDeviceCount(); i++) {
    json += "'temp':{'num_sensor':" + String(i + 1) + ",'value':" + String(sensors.getTempCByIndex(i)) + "},";
  }

  return json;
}

String brightness() {
  int sens = readLED(50);

  return "'light':" + String(sens) + "}";
}

int readLED(int number) { // Read analog value n times and avarage over those n times
  int totaal = 0;
  for (int x = 0; x < number; x++) {
    totaal += analogRead(READ);
    delay(10);
  }
  return totaal / number;
}
