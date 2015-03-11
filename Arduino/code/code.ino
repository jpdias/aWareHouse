#include <OneWire.h>
#include <DallasTemperature.h>

#define DS18B20_PIN 10
#define LUX_PIN A1
#define READ A0

#define RED  2 //this sets the red led pin
#define GREEN  4 //this sets the green led pin
#define BLUE  3 //this sets the blue led pin


OneWire oneWire(DS18B20_PIN);
DallasTemperature sensors(&oneWire);

void setup() {
  pinMode(RED, OUTPUT);
  pinMode(GREEN, OUTPUT);
  pinMode(BLUE, OUTPUT);
  Serial.begin(9600);
  sensors.begin();
}

void loop() {
  setBlue();
  int b = Serial.read();

  if ((char)b == 'r') {
    setGreen();
    String json = "{";
    json += temperature();
    json += brightness() + "}";
    Serial.println(json);
  }
}

void setBlue(){
 digitalWrite(RED, HIGH);         
 digitalWrite(GREEN, HIGH);
 digitalWrite(BLUE, LOW);
}
void setGreen(){
 digitalWrite(BLUE, HIGH);
 digitalWrite(RED, HIGH);
 digitalWrite(GREEN, LOW); 
}
void setRed(){
 digitalWrite(BLUE, HIGH);
 digitalWrite(RED, LOW);
 digitalWrite(GREEN, HIGH); 
}

String temperature() {
  String json;
  sensors.requestTemperatures();
  for (byte i = 0; i < sensors.getDeviceCount(); i++) {
    json += String("'temp':{'num_sensor':" + String(i + 1) + ",'value':" + String(sensors.getTempCByIndex(i)) + "},");
  }

  return json;
}

String brightness() {
  int sens = readLED(50);
  String result;
  result += "'light_sensor':" + String(analogRead(LUX_PIN)) + ",";
  result += "'light':" + String(sens) + "}";
  return result;
}

int readLED(int number) { // Read analog value n times and avarage over those n times
  int totaal = 0;
  for (int x = 0; x < number; x++) {
    totaal += analogRead(READ);
    delay(10);
  }
  return totaal / number;
}
