# CAN Transceiver Design

This document explains the planned CAN interface for the RaceCAN sensor node.

## Purpose

CAN communication allows the sensor node to send telemetry messages to other devices on a vehicle-style network.

The RaceCAN firmware and simulator already use CAN style message IDs. The hardware design adds the physical layer needed for a real CAN bus.

## CAN Architecture

A typical CAN hardware path is:

```text
Microcontroller
     ↓ TX/RX logic
CAN Controller or Peripheral
     ↓
CAN Transceiver
     ↓
CAN_H and CAN_L
     ↓
CAN Bus
```

## Possible Hardware Options

### Option 1: MCP2515 Module

This is beginner friendly. The MCP2515 module communicates with the microcontroller using SPI.

Pros:
- Easy to find
- Common Arduino examples
- Good for learning

Cons:
- Uses multiple SPI pins
- External module or chip needed
- Slower integration than built-in CAN

### Option 2: STM32 with Built-in CAN

This is closer to professional embedded systems.

Pros:
- Built-in CAN controller
- More realistic embedded workflow
- Better for future Formula SAE style work

Cons:
- Harder for beginners
- Requires more setup
- Needs a CAN transceiver

### Option 3: ESP32 TWAI

Some ESP32 boards support CAN-like TWAI controller.

Pros:
- Affordable
- Good software ecosystem
- Powerful microcontroller

Cons:
- Still needs external transceiver
- Pin compatibility varies by board

## CAN Bus Connector

| Pin | Signal |
|-----|--------|
| 1   | CAN_H  |
| 2   | CAN_L  |
| 3   | GND    |

## Termination

A CAN bus normally requires 120 ohm termination at each end of the bus.

The RaceCAN board may include:
- Fixed 120 ohm resistor
- Jumper-selectable 120 ohm resistor
- No onboard termination, documented externally

For a flexible design, jumper-selectable termination is preferred.

## Protection

Future CAN interface protection may include:
- TVS diode array on CAN_H and CAN_L
- Common mode choke
- Series resistors
- ESD protection near connector

## Design Goal

The CAN interface should:
- Match the software CAN protocol
- Be easy to connect
- Include clear labeling
- Support future physical testing
- Be documented well enough to become a KiCad schematic
