# Bill of Materials — Draft

**Project:** RaceCAN-Sensor-Node
**Revision:** Draft Rev A (Day 10)
**Status:** Planned design — **no parts purchased, no PCB fabricated.** Reference designators are indicative until schematic capture (Day 11+).
**Build tier:** Tier B (custom PCB). Tier A breadboard substitutions noted in the last column.

> This is a *draft* BOM produced as a design exercise. Quantities, packages, and MPNs are engineering selections, not a verified purchase order. Prices are intentionally omitted at this stage.

---

## 1. Microcontroller & Clock

| Ref | Category | Part / Value | Example MPN | Package | Qty | Tier A substitute |
| --- | --- | --- | --- | --- | --- | --- |
| U1 | MCU | ATmega328P, 5 V, 10-bit ADC | ATMEGA328P-AU | TQFP-32 | 1 | Arduino Nano module |
| Y1 | Crystal | 16 MHz | ABLS-16.000MHZ | HC-49 SMD | 1 | (on Nano) |
| C1, C2 | Cap | 22 pF (crystal load) | — | 0805 | 2 | (on Nano) |
| J1 | Header | 2×3 ICSP | — | 2.54 mm | 1 | USB on Nano |

## 2. CAN Interface

| Ref | Category | Part / Value | Example MPN | Package | Qty | Tier A substitute |
| --- | --- | --- | --- | --- | --- | --- |
| U2 | CAN controller | MCP2515 (SPI) | MCP2515-I/SO | SOIC-18 | 1 | MCP2515 module |
| U3 | CAN transceiver | MCP2562 | MCP2562-E/SN | SOIC-8 | 1 | TJA1050 (on module) |
| Y2 | Crystal | 8 MHz (MCP2515) | — | HC-49 SMD | 1 | (on module) |
| C3, C4 | Cap | 22 pF | — | 0805 | 2 | (on module) |
| R1 | Resistor | 120 Ω 1 % CAN termination | — | 0805 | 1 | through-hole |
| JP1 | Jumper | Termination enable | — | 2.54 mm | 1 | — |
| L1 | Common-mode choke | CAN CMC | ACT45B-510-2P | SMD | 1 | omit on proto |
| D1 | TVS (CAN) | CAN bus ESD/TVS | PESD1CAN | SOT-23 | 1 | omit on proto |

## 3. Power & Protection

| Ref | Category | Part / Value | Example MPN | Package | Qty | Tier A substitute |
| --- | --- | --- | --- | --- | --- | --- |
| Q1 | P-MOSFET | Reverse-polarity block | DMP3098L-7 | SOT-23 | 1 | SS34 Schottky |
| D2 | TVS | Input load-dump clamp, ~24 V | SMBJ24A | SMB | 1 | — |
| F1 | Fuse | Resettable PTC | — | 1206 | 1 | inline blade fuse |
| FB1 | Ferrite bead | Input EMI | — | 0805 | 1 | omit on proto |
| U4 | Buck reg | 12 V → 5 V | MP1584EN | SOIC-8 | 1 | MP1584 module |
| U5 | LDO | 5 V → 3.3 V | MCP1700-3302E | SOT-23 | 1 | AMS1117-3.3 module |
| C5 | Cap | 10 µF bulk (5 V) | — | 1206 | 1 | — |
| C6 | Cap | 10 µF bulk (3.3 V) | — | 1206 | 1 | — |
| C7–C12 | Cap | 100 nF decoupling (per IC) | — | 0805 | 6 | — |

## 4. Analog Sensing & Input Conditioning

| Ref | Category | Part / Value | Example MPN | Package | Qty | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| R2 | Resistor | 30 kΩ 1 % (divider R1) | — | 0805 | 1 | Battery V sense top leg |
| R3 | Resistor | 10 kΩ 1 % (divider R2) | — | 0805 | 1 | Battery V sense bottom leg |
| RT1 | Thermistor | 10 kΩ NTC, β≈3977 | NTCLE100E3103 | radial | 1 | Temperature sense |
| R4 | Resistor | 10 kΩ 1 % (NTC divider) | — | 0805 | 1 | Pairs with RT1 |
| U6 | Current sensor | Hall, ±20 A analog | ACS712ELCTR-20A-T | SOIC-8 | 1 | ACS712 module |
| R5–R8 | Resistor | 1 kΩ series (input) | — | 0805 | 4 | One per analog channel |
| C13–C16 | Cap | 100 nF RC filter | — | 0805 | 4 | One per analog channel |
| D3–D6 | Clamp diode | Dual Schottky to rails | BAT54S | SOT-23 | 4 | One per analog channel |

## 5. Indicators & Debug

| Ref | Category | Part / Value | Example MPN | Package | Qty | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| D7 | LED | Green — status/heartbeat | — | 0805 | 1 | — |
| D8 | LED | Red — fault state | — | 0805 | 1 | Mirrors fault state machine |
| R9, R10 | Resistor | 1 kΩ LED limit | — | 0805 | 2 | — |
| U7 | USB-UART | Serial debug bridge | CH340N / FT232RL | SOIC | 1 | Feeds dashboard.py / csv_logger.py |

## 6. Connectors

| Ref | Category | Part / Value | Example MPN family | Qty | Notes |
| --- | --- | --- | --- | --- | --- |
| P1 | Power in | Sealed 2-pos | Deutsch DT04-2P | 1 | Locking, sealed |
| P2 | CAN | 4-pos (CANH/CANL/GND/shield) | Deutsch DTM04-4P | 1 | DB9 for bench debug |
| P3 | Sensor I/O | Multi-pos sealed | Deutsch DTM series | 1 | Vibration-rated |

---

## 7. Quantity Roll-up (Tier B)

| Category | Distinct parts | Total pieces |
| --- | --- | --- |
| Active ICs (U1–U7) | 7 | 7 |
| Crystals | 2 | 2 |
| Resistors | — | ~12 |
| Capacitors | — | ~14 |
| Diodes / TVS / clamps | — | ~9 |
| Connectors | 3 | 3 |
| Misc (choke, ferrite, fuse, jumper, header, LEDs) | — | ~7 |

*(Counts are approximate and will firm up after schematic capture.)*

---

## 8. Notes & Disclaimers

- **No procurement has occurred.** This BOM exists to demonstrate component-selection reasoning and to seed a future schematic.
- MPNs are *examples* of suitable parts, not committed line items.
- **Tier A (breadboard)** lets you validate firmware against live signals using off-the-shelf modules before committing to the **Tier B** custom PCB.
- Pricing, distributor part numbers, and footprints will be added once the schematic fixes the design (Day 11+).
- Items flagged Rev B in `component_selection.md` (STM32 MCU, isolated current sensor) are deliberately excluded from this draft.
