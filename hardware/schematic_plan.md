# Schematic Plan

**Project:** RaceCAN-Sensor-Node — Formula SAE / Formula E–style low-voltage CAN telemetry node
**Stage:** Day 11 (schematic planning — paper schematic, no EDA capture or board fabricated yet)
**Status:** Draft net/block plan, feeds future schematic capture and PCB layout

---

## 1. Purpose of This Document

In Day 10 I produced the component selection and a draft BOM — *which* parts implement the architecture and *why*. In Day 11 I turn that parts list into a **block-by-block schematic plan**: I assign a real reference designator to every part, group the parts into functional blocks, and define the named power and signal nets that connect them.

This is the bridge between "a list of parts" and "a schematic I could capture in KiCad and lay out as a PCB." It closes the loop: architecture (Day 9) → parts (Day 10) → schematic plan (Day 11) → layout (later).

> **Honesty note:** I have not captured this in an EDA tool, simulated it, or built it. This is a planned schematic on paper. Everything below is a design intent with reasoning, not a verified circuit.

---

## 2. Locked Design Parameters

These resolve the open items I carried out of Day 10:

| Parameter | Locked value | Reason |
| --- | --- | --- |
| MCU | ATmega328P-AU | `hardware_architecture.md` names no specific MCU; firmware uses 10-bit `0–1023` ADC mapping, which pins it here |
| CAN bitrate | 500 kbit/s | Matches the Day 10 design-anchor table; standard FSAE rate |
| Logic level | 5 V | Reads 0–5 V sensors directly, no level shifting |
| Current-sense range | ACS712-20A (Tier B) | Analog, Arduino-friendly; isolated/higher-range part stays a Rev B item |

---

## 3. Reference Designator Convention

| Prefix | Class | Examples |
| --- | --- | --- |
| U | Integrated circuits | U1 MCU, U2 CAN controller |
| Q | Transistors | Q1 reverse-polarity P-FET |
| D | Diodes (incl. TVS, LEDs) | D1 input TVS, D3 status LED |
| R | Resistors | R8/R9 battery divider |
| C | Capacitors | C1 input bulk |
| L | Inductors / chokes | L1 buck inductor, L2 CAN choke |
| FB | Ferrite bead | FB1 input |
| Y | Crystals | Y1 MCU, Y2 CAN controller |
| F | Fuse | F1 PTC |
| J | Connectors | J1 power, J2 CAN |

---

## 4. Net Naming Convention

**Power nets**

| Net | Meaning |
| --- | --- |
| `VIN_RAW` | Raw +12 V at the input connector, before any protection |
| `VIN_PROT` | Protected +12 V (after reverse-polarity, fuse, ferrite) |
| `+5V` | Main logic rail (buck output) |
| `+3V3` | Sensor / CAN logic rail (LDO output) |
| `GND` | Common ground |

**Signal nets** are named by function (`SPI_SCK`, `CAN_TX`, `ADC_VBAT`, `UART_TX`, etc.) so the schematic reads the same way the firmware does.

---

## 5. Block-by-Block Schematic Plan

### 5.1 Power Input & Protection

| Refdes | Part | Role |
| --- | --- | --- |
| J1 | Sealed 2-pos power connector | +12 V in, GND |
| Q1 | DMP3098L P-FET | Reverse-polarity block (high-side) |
| R1 | 100 Ω | Q1 gate series |
| R2 | 100 kΩ | Q1 gate-source pulldown |
| F1 | PTC resettable fuse | Overcurrent protection |
| FB1 | Ferrite bead | Conducted-noise filter |
| D1 | SMBJ24A TVS | Load-dump / transient clamp |
| C1 | 10 µF | Input bulk capacitor |

**Path:** `J1.1` → `VIN_RAW` → Q1 (source = `VIN_RAW`, drain → F1 → FB1) → `VIN_PROT`. D1 clamps `VIN_PROT` to `GND`. The P-FET blocks current if the battery is connected backwards, with near-zero drop in normal operation — the reverse-battery story I want to be able to defend in an interview.

### 5.2 Voltage Regulation

| Refdes | Part | Role |
| --- | --- | --- |
| U4 | MP1584EN buck | `VIN_PROT` → `+5V` |
| L1 | Buck inductor | Part of the buck switching stage |
| C2 | 10 µF | `+5V` bulk |
| U5 | MCP1700-3302 LDO | `+5V` → `+3V3` |
| C19, C20 | 1 µF each | U5 input/output caps |
| C3 | 10 µF | `+3V3` bulk |

**Path:** `VIN_PROT` → U4 → `+5V` → U5 → `+3V3`. Buck instead of a linear regulator is the thermal-reliability decision from Day 10 (a 7805 would burn ~1.4 W as heat dropping 12 V → 5 V).

### 5.3 Microcontroller (U1 — ATmega328P-AU)

| Refdes | Part | Role |
| --- | --- | --- |
| U1 | ATmega328P-AU | Main MCU, 5 V, 10-bit ADC |
| Y1 | 16 MHz crystal | System clock |
| C15, C16 | 22 pF each | Y1 load caps |
| R3 | 10 kΩ | RESET pullup to `+5V` |
| C4 | 100 nF | VCC decoupling |
| J4 | 2×3 ICSP header | Programming |

**Pin map (Arduino alias → net):**

| MCU pin | Arduino | Net | Function |
| --- | --- | --- | --- |
| PC0 | A0 | `ADC_VBAT` | Battery voltage |
| PC1 | A1 | `ADC_TEMP` | NTC temperature |
| PC2 | A2 | `ADC_THR` | Throttle |
| PC3 | A3 | `ADC_BRK` | Brake |
| PC4 | A4 | `ADC_CURR` | Current sensor |
| PB5 | D13 | `SPI_SCK` | SPI clock to CAN controller |
| PB4 | D12 | `SPI_MISO` | SPI MISO |
| PB3 | D11 | `SPI_MOSI` | SPI MOSI |
| PB2 | D10 | `CAN_CS` | CAN controller chip select |
| PD2 | D2 (INT0) | `CAN_INT` | CAN controller interrupt |
| PD3 | D3 | `LED_STATUS` | Heartbeat LED |
| PD4 | D4 | `LED_FAULT` | Fault-state LED |
| PD0 | RXD | `UART_RX` | Serial from USB-UART |
| PD1 | TXD | `UART_TX` | Serial to USB-UART |
| PC6 | RESET | `RESET` | Reset / ICSP |

### 5.4 CAN Interface

| Refdes | Part | Role |
| --- | --- | --- |
| U2 | MCP2515 | SPI CAN controller |
| Y2 | 8 MHz crystal | U2 reference clock |
| C17, C18 | 22 pF each | Y2 load caps |
| U3 | MCP2562 | CAN transceiver |
| L2 | Common-mode choke | EMI on CANH/CANL |
| R5 | 120 Ω 1 % | Bus termination (jumper-selectable) |
| D2 | PESD1CAN | CAN bus TVS |
| J2 | Sealed 4-pos / DB9 bench | CANH, CANL, GND, shield |
| C5, C6 | 100 nF each | U2, U3 decoupling |

**Path:** U1 ↔ U2 over SPI (`SPI_SCK/MOSI/MISO`, `CAN_CS`, `CAN_INT`). U2 `TXCAN/RXCAN` → U3 `TXD/RXD` (`CAN_TX`, `CAN_RX`). U3 `CANH/CANL` → L2 → J2, with R5 termination and D2 clamp at the connector. The MCP2562 `VIO` pin ties to `+5V` here, keeping the logic interface clean. Termination is on a jumper because only the two physical ends of a CAN bus should be terminated.

### 5.5 Analog Input Conditioning

Every analog channel uses the same protection chain from Day 9: series resistor → RC filter to ground → Schottky clamp to the rails, so the ADC pin never sees something damaging.

| Channel | Sense element | Series R | Filter C | Clamp | ADC net |
| --- | --- | --- | --- | --- | --- |
| Battery V | R8 = 30 kΩ / R9 = 10 kΩ 1 % divider | R11 = 1 kΩ | C10 = 100 nF | D5 (BAT54S) | `ADC_VBAT` |
| Temperature | NTC + R10 = 10 kΩ 1 % | R12 = 1 kΩ | C11 = 100 nF | D6 | `ADC_TEMP` |
| Throttle | External 0–5 V (via J3) | R13 = 1 kΩ | C12 = 100 nF | D7 | `ADC_THR` |
| Brake | External 0–5 V (via J3) | R14 = 1 kΩ | C13 = 100 nF | D8 | `ADC_BRK` |
| Current | U6 ACS712-20A `VIOUT` | R15 = 1 kΩ | C14 = 100 nF | D9 | `ADC_CURR` |

| Refdes | Part | Role |
| --- | --- | --- |
| U6 | ACS712ELCTR-20A | Hall current sensor; high-current path through `IP+`/`IP-` at J3, analog `VIOUT` to `ADC_CURR` |
| J3 | Deutsch DTM | Sensor I/O harness in |

The battery divider keeps its iconic 30 k / 10 k (÷4) values — now formally R8 and R9 on the board. The 1 % tolerance on the divider and NTC reference resistor is the safety-logic decision: at ÷4, sloppy resistors can shift the reported pack voltage enough to mask or false-trip an overvoltage fault.

### 5.6 Indicators & Debug

| Refdes | Part | Role |
| --- | --- | --- |
| D3 | Green LED + R6 (1 kΩ) | Heartbeat / node alive |
| D4 | Red LED + R7 (1 kΩ) | Mirrors firmware fault state |
| U7 | CH340 USB-UART | Bridges `UART_TX/RX` to the host |
| J5 | USB connector | Feeds `dashboard.py` / `csv_logger.py` over serial |

The USB-UART is what lets the Python dashboard and CSV logger from Days 1–9 actually receive live data from the physical node.

---

## 6. Reference Designator Index

| Refdes | Part | Block |
| --- | --- | --- |
| U1 | ATmega328P-AU | MCU |
| U2 | MCP2515 | CAN controller |
| U3 | MCP2562 | CAN transceiver |
| U4 | MP1584EN | 12 V → 5 V buck |
| U5 | MCP1700-3302 | 5 V → 3.3 V LDO |
| U6 | ACS712-20A | Current sensor |
| U7 | CH340 | USB-UART |
| Q1 | DMP3098L | Reverse-polarity P-FET |
| D1 | SMBJ24A | Input TVS |
| D2 | PESD1CAN | CAN TVS |
| D3 | Green LED | Status |
| D4 | Red LED | Fault |
| D5–D9 | BAT54S | ADC channel clamps |
| Y1 | 16 MHz crystal | MCU clock |
| Y2 | 8 MHz crystal | CAN controller clock |
| L1 | Buck inductor | Regulation |
| L2 | Common-mode choke | CAN EMI |
| FB1 | Ferrite bead | Input filter |
| F1 | PTC fuse | Overcurrent |
| R1, R2 | 100 Ω / 100 kΩ | Q1 gate network |
| R3 | 10 kΩ | RESET pullup |
| R5 | 120 Ω 1 % | CAN termination |
| R6, R7 | 1 kΩ | LED series |
| R8, R9 | 30 kΩ / 10 kΩ 1 % | Battery divider |
| R10 | 10 kΩ 1 % | NTC reference |
| R11–R15 | 1 kΩ | ADC channel series |
| C1–C3 | 10 µF | Rail bulk |
| C4–C6 | 100 nF | IC decoupling |
| C10–C14 | 100 nF | ADC RC filters |
| C15–C18 | 22 pF | Crystal load |
| C19, C20 | 1 µF | LDO in/out |
| J1 | Power connector | Input |
| J2 | CAN connector | Bus |
| J3 | Sensor connector | Analog I/O |
| J4 | ICSP header | Programming |
| J5 | USB connector | Debug |

---

## 7. Open Items → carried to Day 12

- Capture this plan in KiCad and run an electrical-rules check (ERC).
- Confirm MP1584EN feedback divider values for an exact 5.0 V output.
- Decide whether `CAN_INT` is used or polled (affects PD2 allocation).
- Day 12: PCB placement / layout planning — grouping, ground strategy, and connector edge placement.
