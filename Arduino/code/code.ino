#include <OneWire.h>
#include <DallasTemperature.h>
#include <DHT.h>

#define DS18B20_PIN 10
#define LUX_PIN A1
#define READ A0
#define DHT_PIN A2
#define SOUND_PIN A3

#define RED 2
#define GREEN 4
#define BLUE 3

#define DHTTYPE DHT11

OneWire oneWire(DS18B20_PIN);
DallasTemperature sensors(&oneWire);
DHT dht(DHT_PIN, DHTTYPE);

void setup() {
  pinMode(RED, OUTPUT);
  pinMode(GREEN, OUTPUT);
  pinMode(BLUE, OUTPUT);
  Serial.begin(9600);
  sensors.begin();
  dht.begin();
}

void loop() {
 setBlue();

 int b = Serial.read();

 if ((char)b == 'r') {
    setGreen();

    float h = dht.readHumidity();
    float t = dht.readTemperature();
    float f = dht.readTemperature(true);
    float hi = fahrenheit_to_celsius(dht.computeHeatIndex(f, h));

    String json = "[{'points':[[";
    json += temperature() + "," + t +  "," + h + "," + hi + "," + brightness() + "]],";
    json += String("'name': 'sensors', 'columns': ['temp1', 'temp2', 'humidity', 'heat_index', 'light_sensor', 'light']},");
    json += "{'points':[[";
    json += String(readSound(5)) + "]],";
    json += String("'name': 'sensors_fast', 'columns': ['sound']}]");
    Serial.println(json);
  } else if ((char)b == 'x') {
    setYellow();
    String json = "[{'points':[[";
    json += String(readSound(5)) + "]],";
    json += String("'name': 'sensors_fast', 'columns': ['sound']}]");
    Serial.println(json);
  }
}

void setBlue() {
  digitalWrite(RED, HIGH);
  digitalWrite(GREEN, HIGH);
  digitalWrite(BLUE, LOW);
}

void setGreen() {
  digitalWrite(BLUE, HIGH);
  digitalWrite(RED, HIGH);
  digitalWrite(GREEN, LOW);
}

void setRed() {
  digitalWrite(BLUE, HIGH);
  digitalWrite(RED, LOW);
  digitalWrite(GREEN, HIGH);
}

void setYellow() {
  digitalWrite(BLUE, HIGH);
  digitalWrite(RED, LOW);
  digitalWrite(GREEN, LOW);
}

String temperature() {
  String json;
  sensors.requestTemperatures();
  for (byte i = 0; i < sensors.getDeviceCount(); i++) {
    json += String(sensors.getTempCByIndex(i));
  }

  return json;
}

String brightness() {
  int sens = readLED(50);
  String result;
  result +=  String(analogRead(LUX_PIN)) + ","; // Light Sensor
  result +=  String(sens); // Inverse LED
  return result;
}

int readSound(int number) {
  int total = 0;

  for (int x = 0; x < number; ++x) {
    total += analogRead(SOUND_PIN);
    delay(100);
  }
  
  return 1023 - total / number;
}

int readLED(int number) { // Read analog value n times and average over those n times
  int total = 0;

  for (int x = 0; x < number; ++x) {
    total += analogRead(READ);
    delay(10);
  }

  return total / number;
}

float fahrenheit_to_celsius(float f) {
  return (f - 32.0f) / 1.8f;  
}

