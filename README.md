# RaceCAN Digital Kit

RaceCAN Digital Kit is a digital engineering kit for learning CAN based low voltage telemetry systems used in motorsports, robotics, and Formula SAE style projects.

The project models a low voltage sensor node that reads vehicle style signals, detects warning and fault conditions, sends telemetry using a CAN style message protocol, displays live data through a dashboard, and logs data to CSV.

## Project Purpose

This project is being built to develop practical skills in:

1. Hardware system design
2. Firmware style logic
3. CAN communication
4. Sensor data modeling
5. Fault detection
6. Python dashboard software
7. Data logging
8. Technical documentation
9. Digital product development

## Why This Matters

Low voltage electronics teams in electric vehicle and Formula SAE style systems rely on sensor data, fault handling, and communication between modules.

RaceCAN Digital Kit models those ideas in a way that can be studied, simulated, modified, and eventually extended into real firmware and PCB hardware.

## Current Working Demo

RaceCAN currently includes a working Python simulator and terminal dashboard.

The simulator generates CAN style telemetry messages for:

1. Battery voltage
2. Temperature
3. Throttle position
4. Brake position
5. Current draw
6. Fault states
7. Heartbeat status

The dashboard displays:

1. Live telemetry values
2. System state
3. Active faults
4. Recent CAN style messages
5. CSV logging output

## V1 Simulated Signals

| Signal | Unit | Description |
|---|---|---|
| Battery voltage | V | Simulated low voltage battery voltage |
| Temperature | C | Simulated board or system temperature |
| Throttle position | Percent | Simulated driver throttle input |
| Brake position | Percent | Simulated driver brake input |
| Current draw | A | Simulated electrical current draw |
| External fault | Boolean | Simulated external fault condition |

## CAN Style Messages

| CAN ID | Message Name | Purpose |
|---|---|---|
| 0x100 | Heartbeat | Confirms that the node is alive |
| 0x101 | Voltage Status | Sends battery voltage and voltage faults |
| 0x102 | Temperature Status | Sends temperature and temperature faults |
| 0x103 | Driver Inputs | Sends throttle and brake values |
| 0x104 | Current Status | Sends current draw and current faults |
| 0x105 | Fault Status | Sends active fault flags |

## Project Structure

```text
RaceCAN-Sensor-Node/
  docs/
    can_protocol.md
    cli_usage.md
    data_model.md
    dashboard_plan.md
    fault_logic.md
    future_roadmap.md
    product_overview.md
    project_summary.md
    simulator_plan.md
    system_architecture.md
    testing_checklist.md
    v1_requirements.md

  software/
    simulator/
      simulator.py
      config.py
      fault_logic.py
      message_encoder.py
      requirements.txt

    dashboard/
      dashboard.py
      csv_logger.py
      racecan_log.csv

  hardware/
    README.md

  firmware/
    README.md

  images/

## Hardware Architecture

RaceCAN includes hardware architecture documentation for a future CAN based low voltage telemetry PCB.

The hardware design plan includes:

1. Sensor input circuits
2. Power input protection
3. Voltage regulation
4. CAN transceiver design
5. Connector planning
6. Pin mapping
7. Test point planning
8. Future KiCad schematic preparation

Hardware documentation is located in:

```text
hardware/
docs/hardware_architecture.md
docs/pin_mapping.md
docs/connector_plan.md
```

The current hardware layer is documentation only. Future work will add KiCad schematic and PCB layout files.

RaceCAN now includes an Arduino style firmware template that models how the telemetry node logic could run on a physical microcontroller.

The firmware template includes:

1. Sensor input reading
2. Engineering unit conversion
3. Fault detection
4. Status and fault outputs
5. CAN style message formatting
6. Placeholder CAN transmission
7. Serial debug output

Firmware location:

```text
firmware/racecan_firmware_template/
