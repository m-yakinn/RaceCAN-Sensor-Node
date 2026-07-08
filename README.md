# RaceCAN Sensor Node

A digital engineering portfolio project modelling a CAN-based low-voltage telemetry sensor node of the type used in Formula SAE and Formula E vehicles. The project is design-first: all architecture, simulation, firmware, and hardware documentation is fully developed and validated before any KiCad capture or physical fabrication begins.

Built by Mohammad Yakin as a learning and interview preparation project targeting Formula E and FSAE embedded systems roles.

---

## What This Project Demonstrates

- CAN protocol design: message framing, fixed-point encoding, little-endian byte order
- Fault detection and state machine design: warning, critical, latched-fault, shutdown
- Battery management system (BMS) simulation: cell monitoring, Coulomb-counted SOC, active-high shutdown signal
- Hardware architecture: component selection, protection circuits, PCB floorplanning
- Firmware logic: sensor reading, fault evaluation, CAN transmission on ATmega328P
- Software simulation: Python simulator, terminal dashboard, CSV logging, test harness

---

## System Architecture

```
                    Vehicle Battery (12 V nominal)
                            |
                     [Reverse Polarity]
                            |
                   [MP1584EN Buck → 5 V]
                            |
                   [MCP1700 LDO → 3.3 V]
                            |
          +-----------------+-----------------+
          |                 |                 |
    [ACS712-20A]     [ATmega328P-AU]    [MCP2515 CAN Ctrl]
    Current sense      MCU (8 MHz)      SPI @ 4 MHz
          |                 |                 |
          +----ADC----------+            [MCP2562 CAN TXV]
          |                 |                 |
    [Thermistor]      [Fault logic]      [CAN Bus 500 kbit/s]
    [Voltage div]     [Encoder]          0x100-0x105 + 0x200-0x205
          |                 |
    [Throttle/Brake]  [CH340 USB-Serial]
```

---

## CAN Protocol

### Primary Telemetry Frames (Node → Bus)

| Frame ID | Name            | Signals                                      | Rate    |
|----------|-----------------|----------------------------------------------|---------|
| 0x100    | HEARTBEAT       | node_id, uptime_s, system_state, fw_version  | 100 ms  |
| 0x101    | VOLTAGE_STATUS  | battery_voltage_mv, voltage_fault            | 100 ms  |
| 0x102    | TEMP_STATUS     | temperature_dC, temp_fault                   | 100 ms  |
| 0x103    | DRIVER_INPUTS   | throttle_pct (x100), brake_pct (x100)        | 100 ms  |
| 0x104    | CURRENT_STATUS  | current_ma (int16), current_fault            | 100 ms  |
| 0x105    | FAULT_STATUS    | fault_flags (bitmask), system_state_code     | 100 ms  |

### BMS Extension Frames (0x200–0x205)

| Frame ID | Name              | Signals                                             |
|----------|-------------------|-----------------------------------------------------|
| 0x200    | BMS_PACK_STATUS   | pack_voltage_mv, min_cell_mv, max_cell_mv, delta_mv |
| 0x201    | BMS_CURRENT       | current_ma (int16), soc_percent, shutdown_signal, system_state |
| 0x202    | BMS_TEMPERATURE   | temperature_dC (int16), fault_count                 |
| 0x203    | BMS_CELL_VOLTAGES | cell_0_mv … cell_3_mv (uint16, zero-padded for 3S)  |
| 0x204    | BMS_FAULT_FLAGS   | fault_bits (uint8 bitmask), highest_severity        |
| 0x205    | BMS_SOC_EXTENDED  | accumulated_charge_mah, capacity_mah, chemistry, num_cells |

**Encoding convention (all frames):** fixed-point scaling, little-endian byte order, int16 for signed values, uint16/uint8 for unsigned. DLC = 8 for all frames.

### Fault Thresholds

| Parameter | Warning | Critical |
|-----------|---------|----------|
| Battery voltage | 11.0 V | 10.5 V |
| Temperature | 50 C | 60 C |
| Current | 12.0 A | 15.0 A |

---

## Hardware Design

All hardware work is documentation-only. KiCad capture is a future phase.

| Component | Part | Purpose |
|-----------|------|---------|
| MCU | ATmega328P-AU | Main controller, SPI master, ADC |
| CAN controller | MCP2515 | SPI-to-CAN, interrupt-driven receive |
| CAN transceiver | MCP2562 | Differential bus driver, 500 kbit/s |
| Buck regulator | MP1584EN | 12 V → 5 V, up to 3 A |
| LDO | MCP1700 | 5 V → 3.3 V, low-dropout |
| Current sensor | ACS712-20A | ±20 A hall-effect, 100 mV/A |
| USB-serial | CH340 | Debug and firmware upload |

**Protection:** reverse polarity (P-channel MOSFET), TVS diodes on CAN lines, bulk and local decoupling capacitors, input fuse.

**PCB:** 2-layer 1.6 mm FR4, single continuous ground plane, five-zone floorplan. Buck regulator and analog front end placed in diagonally opposite corners to isolate switching noise from sensitive analog signals.

---

## Repository Structure

```
RaceCAN-Sensor-Node/
  software/
    simulator/
      simulator.py           # Telemetry simulator (normal/warning/fault modes)
      config.py              # Node ID, timing constants
      fault_logic.py         # Fault evaluation and state machine
      message_encoder.py     # Pack telemetry into CAN frame dicts
      bms_simulator.py       # BMS: cell monitoring, SOC, fault state machine
      bms_to_can.py          # Encode BMSState into CAN frames 0x200-0x205
      test_cases.py          # Protocol unit tests (34 cases)
      test_cases_bms.py      # BMS simulator tests (14 cases)
      test_bms_to_can.py     # BMS-to-CAN integration tests (17 cases)
      integration_example.py # End-to-end demo: BMS -> CAN -> decoder

    dashboard/
      dashboard.py           # Terminal dashboard (curses)
      dashboard_receiver.py  # Receiver-side decoder with dashboard integration
      csv_logger.py          # CSV telemetry logging

  firmware/
    racecan_firmware.ino     # Arduino-style firmware template (ATmega328P)
    dashboard_receiver_example.c  # C receiver-side decoder example

  hardware/
    bom.md                   # Bill of materials with part numbers
    schematic_plan.md        # Schematic intent, all nets named
    netlist.md               # Logical netlist
    placement_plan.md        # PCB floorplan and per-block placement intent
    layout_guidelines.md     # Routing rules, ground strategy, clearances
    protection_analysis.md   # Threat model, fault-current math, TVS selection
    pin_mapping.md           # ATmega328P pin assignments
    connector_plan.md        # Connector types and pinouts
    hardware_architecture.md # Top-level hardware architecture

  docs/
    can_message_map.md       # Full CAN message specification
    can_protocol.md          # Protocol design decisions
    fault_logic.md           # Fault logic and threshold rationale
    system_architecture.md   # System-level architecture
    future_roadmap.md        # Phase roadmap
    receiver_validation.md   # Receiver-side validation documentation
    test_matrix.md           # 34-case test matrix
    day01_progress.md        # ... through ...
    day20_progress.md        # Daily progress logs
```

---

## Running the Simulator

```bash
# Clone the repo
git clone https://github.com/m-yakinn/RaceCAN-Sensor-Node.git
cd RaceCAN-Sensor-Node

# Install dependencies
pip install -r software/simulator/requirements.txt

# Run in normal mode (continuous)
python software/simulator/simulator.py --mode normal

# Run in fault mode for 10 cycles
python software/simulator/simulator.py --mode fault --cycles 10

# Run the BMS simulator demo
python software/simulator/bms_simulator.py

# Run the BMS-to-CAN integration example
python software/simulator/integration_example.py
```

## Running the Tests

```bash
# Protocol unit tests (34 cases)
python software/simulator/test_cases.py

# BMS simulator tests (14 cases)
python software/simulator/test_cases_bms.py

# BMS-to-CAN integration tests (17 cases)
python software/simulator/test_bms_to_can.py
```

---

## BMS Simulator

The BMS simulator models a 3S or 4S low-voltage pack (LiPo or LiFePO4) with:

- Individual cell voltage monitoring
- Coulomb-counted state of charge (SOC)
- Five-state fault machine: NORMAL → WARNING → CRITICAL → LATCHED_FAULT → SHUTDOWN
- Active-high shutdown signal generation
- 8 fault types: cell OV, cell UV, pack OC charge, pack OC discharge, overtemperature, cell imbalance, low SOC, internal error

```python
from software.simulator.bms_simulator import create_lipo_3s
from software.simulator.bms_to_can import BMSToCANEncoder, BMSCANDecoder

bms     = create_lipo_3s(capacity_mah=2500)
encoder = BMSToCANEncoder()
decoder = BMSCANDecoder()

bms.update_cells([3.75, 3.70, 3.72])
bms.update_current(5.0)
bms.update_temperature(40.0)
state = bms.update()

frames = encoder.encode(state)
for frame in frames:
    decoded = decoder.decode(frame["frame_id"], frame["data"])
    print(f"0x{frame['frame_id']:03X}: {decoded}")
```

---

## Fault State Machine

```
         NORMAL
           |
    (warning fault)
           |
         WARNING
           |
    (critical fault)
           |
         CRITICAL -------> LATCHED_FAULT
           |                     |
      shutdown=1            shutdown=1
                          (persists until
                           manual reset)
```

A critical fault latches the system in LATCHED_FAULT. Values returning to safe ranges do not auto-clear the fault. This models the real-vehicle behavior where the driver or pit crew must acknowledge the fault before the car can continue.

---

## Honest Status

- Software simulation: complete (Days 1–20)
- Firmware template: complete (Days 13–14, Arduino-style, not compiled for hardware)
- Hardware documentation: complete (Days 10–12, schematics and layout are intent documents, not KiCad files)
- KiCad schematic and PCB layout: not yet started (requires KiCad desktop tool)
- Physical build and validation: not yet started (requires component purchase)

The board has not been fabricated or tested on hardware.
---

## Interview Positioning

The core talking point for this project:

> "An undetected fault in a low-voltage telemetry node is a failure even when nothing burns. I designed the fault detection, state machine, and shutdown logic in software first so I could test every boundary condition before touching hardware. The BMS state machine latches on a critical fault and requires a manual reset — the same behavior real Formula E systems use to prevent a transient fault from auto-clearing and allowing the car to continue in an unsafe state."

---
