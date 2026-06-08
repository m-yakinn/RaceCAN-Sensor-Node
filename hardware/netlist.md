# Netlist (Planned)

**Project:** RaceCAN-Sensor-Node
**Stage:** Day 11 — planned netlist derived from `schematic_plan.md`
**Status:** Draft. Decoupling caps are grouped under their rail rather than listed per-IC.

> This is a planned netlist, not an EDA-exported one. It lists the named nets and their primary nodes so the schematic can be captured consistently.

---

## Power Nets

| Net | Primary nodes | Notes |
| --- | --- | --- |
| `VIN_RAW` | J1.1, Q1.S, R1 | Raw +12 V, before protection |
| `VIN_PROT` | Q1.D → F1 → FB1, U4.IN, D1.A, R8 (divider top), U6.VCC path | Protected +12 V |
| `+5V` | U4.OUT, U5.IN, U1.VCC, U2.VDD, U3.VDD, U3.VIO, U6.VCC, R3, R5 jumper ref | Main logic rail |
| `+3V3` | U5.OUT, C3 | Sensor / aux 3.3 V rail |
| `GND` | All block grounds, J1.2, J2.GND, C-bank returns, D-clamp cathodes/anodes to GND | Common ground |

---

## Signal Nets — SPI (MCU ↔ CAN controller)

| Net | Nodes |
| --- | --- |
| `SPI_SCK` | U1.PB5 (D13) — U2.SCK |
| `SPI_MOSI` | U1.PB3 (D11) — U2.SI |
| `SPI_MISO` | U1.PB4 (D12) — U2.SO |
| `CAN_CS` | U1.PB2 (D10) — U2.CS |
| `CAN_INT` | U1.PD2 (INT0) — U2.INT |

## Signal Nets — CAN (controller ↔ transceiver ↔ bus)

| Net | Nodes |
| --- | --- |
| `CAN_TX` | U2.TXCAN — U3.TXD |
| `CAN_RX` | U2.RXCAN — U3.RXD |
| `CANH` | U3.CANH — L2 — R5 — D2 — J2.1 |
| `CANL` | U3.CANL — L2 — R5 — D2 — J2.2 |

## Signal Nets — Analog ADC channels

| Net | Nodes |
| --- | --- |
| `ADC_VBAT` | R8/R9 midpoint — R11 — C10 — D5 — U1.PC0 (A0) |
| `ADC_TEMP` | NTC/R10 midpoint — R12 — C11 — D6 — U1.PC1 (A1) |
| `ADC_THR` | J3 (throttle) — R13 — C12 — D7 — U1.PC2 (A2) |
| `ADC_BRK` | J3 (brake) — R14 — C13 — D8 — U1.PC3 (A3) |
| `ADC_CURR` | U6.VIOUT — R15 — C14 — D9 — U1.PC4 (A4) |

## Signal Nets — Serial debug

| Net | Nodes |
| --- | --- |
| `UART_TX` | U1.PD1 (TXD) — U7.RXD |
| `UART_RX` | U1.PD0 (RXD) — U7.TXD |

## Signal Nets — Indicators

| Net | Nodes |
| --- | --- |
| `LED_STATUS` | U1.PD3 (D3) — R6 — D3(LED) — GND |
| `LED_FAULT` | U1.PD4 (D4) — R7 — D4(LED) — GND |

## Signal Nets — Clocks & Reset

| Net | Nodes |
| --- | --- |
| `XTAL1` | U1.PB6 — Y1 — C15 — GND |
| `XTAL2` | U1.PB7 — Y1 — C16 — GND |
| `CANOSC1` | U2.OSC1 — Y2 — C17 — GND |
| `CANOSC2` | U2.OSC2 — Y2 — C18 — GND |
| `RESET` | U1.PC6 — R3 (to +5V) — J4.5 |

---

## Connector Pinout Summary

| Connector | Pin | Net |
| --- | --- | --- |
| J1 (Power) | 1 / 2 | `VIN_RAW` / `GND` |
| J2 (CAN) | 1 / 2 / 3 / 4 | `CANH` / `CANL` / `GND` / shield |
| J3 (Sensor I/O) | per channel | throttle, brake, current `IP+/IP-`, GND |
| J4 (ICSP) | 1–6 | MISO, +5V, SCK, MOSI, RESET, GND |
| J5 (USB) | — | to U7 (CH340) |
