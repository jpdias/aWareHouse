#include <OneWire.h>            // OneWire-Bibliothek einbinden
#include <DallasTemperature.h>  // DS18B20-Bibliothek einbinden

#define DS18B20_PIN 10   // Pin für DS18B20 definieren Arduino D2
#define READ A0
int basis = 0;

OneWire oneWire(DS18B20_PIN);          // OneWire Referenz setzen
DallasTemperature sensors(&oneWire);   // DS18B20 initialisieren


void setup() {

  pinMode(LED, OUTPUT);
  Serial.begin(9600);
  sensors.begin();  // DS18B20 starten
  //Serial.println(sensors.getDeviceCount());
}


void loop() {

  int b = Serial.read();
  String json = "{";

  //if ((char)b == 'r') {

    sensors.requestTemperatures(); // Temperatursensor(en) auslesen
    for (byte i = 0; i < sensors.getDeviceCount(); i++) {	// Temperatur ausgeben
      json += show_temperature(i + 1, sensors.getTempCByIndex(i));
    }
    json += brightness()+"}";
    Serial.println(json);
    
    delay(100);
  //}
}

String show_temperature(byte num, float temp) {
  String result = "'temp':{'num_sensor':";
  result += num;
  result += ",'value':";
  result += temp;
  result += "},";
  return result;
}

String brightness() {
  int sens = readLED(50);
  String result = "";
  basis = sens - 20;                 // setting sensitivity - now it will react if the LED is 20 lower than the setting above
  //for(int y = 0; y < 1000; y++) {    // after every 1000 tests the program will reset the led to cope with changing light
  sens = readLED(50);
  if (sens < basis) {               // testing is the led was in the dark
    result += "'light':{'light':false,'value':";
    result += sens;
    result += "},";
  }
  else {
    result += "'light':{'light':true,'value':"; result += sens; result += "}";
  }
  //}
  return result;
}

int readLED(int number) {            // Read analog value n times and avarage over those n times
  int totaal = 0;
  for (int x = 0; x < number; x++) {
    totaal += analogRead(READ);
    delay(10);
  }
  return totaal / number;
}
