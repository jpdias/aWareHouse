### aWareHouse

We are in the rise of IoT (Internet of Things). A world where everything is connected and we can, with simple tools, monitor and control everything. In this context, there is a lot of room to a more recurrent use of diferent programming paradigms: from the hardware to the cloud, there is a need to interact with many diferent layers of system architecture for a single application.

This application, aWareHouse, was designed with the objective of, with a simple interface, we can monitor a house or a warehouse in terms of environment conditions (temperature, humidity, sound and luminosity).

To accomplish this it's used a combination of hardware/software and different programming languages, in a way that gave us a robust application that can be used to congure a warning system when there are changes in the environment, to take decisions analysing the past conditions and the relations with external (meteorological) conditions or simply to monitor the current conditions inside our warehouse.

### Software Dependencies

* [InfluxDB](https://influxdb.com/)
An open-source distributed time series database.
    - For installing it on Raspberry Pi (ARM processor) follow this [tutorial](http://www.pihomeserver.fr/en/2014/11/29/raspberry-pi-home-server-installer-influxdb/)

* [Python 2.7.x](https://www.python.org/downloads/)
    - The additional requirements are in ``Server\requirements.txt`` file and can be installed using ``pip install -r requirements.txt``

### Hardware Dependencies

* Linux based machine (in this case was used an Raspberry Pi 1 model B)
* Arduino (in this case was used an Arduino Nano)
    - Breadboard
    - DHT11 (Temperature / Humidity)
    - DS18B20 (Temperature)
    - LM393 (Sound level)
    - Diffused LED
    - Photo cell / Photoresistor
    - Some resistors
    - Wires
    
![Circuit example](http://i.imgur.com/VbYlxQS.png)
    
### Screenshots

![Dashboard](http://i.imgur.com/PWtn9HJ.png)

![Configuration Dashboard](http://i.imgur.com/OEHvK1U.png)

### Authors

* [Duarte Duarte](http://github.com/dduarte) 
* [Hugo Freixo](http://github.com/freixo) 
* [João Pedro Dias](http://github.com/jpdias) 
