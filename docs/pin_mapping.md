# Pin Mapping

This document defines the planned microcontroller pin mapping for the RaceCAN sensor node.

## Prototype Pin Map

The first firmware template uses an Arduino-style pin map.

| Function | Pin | Type | Notes |
|---|---|---|---|
| Throttle input | A0 | Analog input | Simulated throttle sensor |
| Brake input | A1 | Analog input | Simulated brake sensor |
| Battery voltage input | A2 | Analog input | Scaled voltage divider input |
| Temperature input | A3 | Analog input | Thermistor input |
| Current input | A4 | Analog input | Current sensor input |
| External fault input | D2 | Digital input | Uses pull-up logic |
| Shutdown output | D11 | Digital output | Goes active during critical fault |
| Fault LED | D12 | Digital output | Indicates fault state |
| Status LED | D13 | Digital output | Indicates firmware is running |

## CAN Interface Pins

A future MCP2515 CAN module version may use SPI pins.

| Function | Arduino Uno/Nano Pin | Notes |
|---|---|---|
| MCP2515 CS | D10 | SPI chip select |
| MCP2515 MOSI | D11 | SPI data from MCU to CAN controller |
| MCP2515 MISO | D12 | SPI data from CAN controller to MCU |
| MCP2515 SCK | D13 | SPI clock |
| MCP2515 INT | D3 | Interrupt from CAN controller |

## Important Design Note

Pins D11, D12, and D13 are shared with SPI on Arduino Uno/Nano.

Because of this, the current firmware template pins for shutdown, fault LED, and status LED may need to move in a physical MCP2515 implementation.

A revised physical design may use:

| Function | Revised Pin |
|---|---|
| Shutdown output | D4 |
| Fault LED | D5 |
| Status LED | D6 |
| MCP2515 CS | D10 |
| MCP2515 INT | D3 |

## Future Improvement

When the board is moved into KiCad, the final pin map should be updated based on the selected microcontroller and CAN hardware.
