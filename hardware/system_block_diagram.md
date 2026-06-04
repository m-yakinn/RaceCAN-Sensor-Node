# System Block Diagram

This document contains the text-based system block diagram for the RaceCAN sensor node hardware.

## Hardware Block Diagram

```text
           +----------------------+
           |      Power Input     |
           |      VIN + GND       |
           +----------+-----------+
                      |
                      v
           +----------------------+
           | Protection Circuit   |
           | Fuse / TVS / Diode   |
           +----------+-----------+
                      |
                      v
           +----------------------+
           | Voltage Regulation   |
           | 5V / 3.3V Rails      |
           +----------+-----------+
                      |
                      v
+----------------+    +----------------------+    +----------------+
| Sensor Inputs  | -> |   Microcontroller    | -> | CAN Interface  |
| Voltage        |    | ADC / GPIO / Logic   |    | Transceiver    |
| Temperature    |    | Fault Detection      |    | CAN_H / CAN_L  |
| Throttle       |    | Message Formatting   |    +----------------+
| Brake          |    +----------+-----------+
| Current        |               |
+----------------+               v
                       +---------------------+
                       | Status / Fault I/O  |
                       | LEDs / Shutdown Out |
                       +---------------------+
