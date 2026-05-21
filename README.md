# RaceCAN Sensor Node

RaceCAN Sensor Node is a CAN based low voltage telemetry board designed for motorsports, robotics, and Formula SAE style systems.

The goal of this project is to build a small embedded sensor node that can read vehicle style sensor data, detect fault conditions, transmit telemetry over CAN bus, and log data to a dashboard.

This project is being built to strengthen my skills in PCB design, embedded firmware, CAN communication, sensor interfacing, and low voltage electrical systems.

## V1 Features

RaceCAN Sensor Node V1 will include:

1. Battery voltage sensing
2. Thermistor temperature sensing
3. Potentiometer input to simulate throttle or brake position
4. Digital fault input
5. CAN bus telemetry output
6. Fault detection logic
7. Status LED
8. Fault LED
9. Shutdown output pin
10. Python based serial or CAN dashboard

## System Overview

Sensors:
- Battery voltage input
- Thermistor input
- Throttle or brake potentiometer
- Digital fault input

Microcontroller:
- Reads sensor values
- Filters raw data
- Detects fault conditions
- Packages CAN messages

CAN Transceiver:
- Sends telemetry over CAN bus

Receiver Node or USB CAN Adapter:
- Reads CAN messages
- Sends data to laptop

Python Dashboard:
- Displays live values
- Logs data to CSV
