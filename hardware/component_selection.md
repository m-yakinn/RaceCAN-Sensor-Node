# Component Selection

**Project:** RaceCAN-Sensor-Node — Formula SAE / Formula E–style low-voltage CAN telemetry node
**Stage:** Day 10 (design selection — no parts purchased; this is a documented design exercise)
**Status:** Draft / proposed selections, pending schematic capture

---

## 1. Purpose of This Document

Days 1–9 defined *what* the node does: read analog sensors (battery voltage, temperature, throttle, brake, current), run fault logic, and broadcast telemetry on a CAN bus using message IDs `0x100`–`0x105`. This document defines *what physical parts would implement that architecture*, and — more importantly — **why each part was chosen** over the alternatives.

Every selection below is justified on three axes that matter on a race car:

- **Function** — does it meet the electrical requirement?
- **Reliability** — does it survive vibration, heat, and a noisy 12 V automotive electrical environment?
- **Serviceability / cost** — is it sane to assemble, debug, and replace?

> **Honesty note:** Nothing here has been purchased, fabricated, or bench-tested. These are engineering selections with rationale. Any part marked *alternative* was considered but not chosen.

---

## 2. Design Anchors (carried over from Days 1–9)

| Anchor | Value | Source |
| --- | --- | --- |
| Logic family | 5 V | ATmega328P-class MCU |
| ADC resolution | 10-bit (0–1023) | Throttle/brake mapping in firmware |
| Input supply | Nominal 12 V automotive | Hardware architecture doc |
| Bus | Single CAN channel, 500 kbit/s (typical FSAE) | CAN message map |
| Battery voltage sense | R1 = 30 kΩ, R2 = 10 kΩ → ÷4 (12 V → ~3 V) | Day 9 |
| Signals | Voltage, temperature (NTC), throttle %, brake %, current | Day 9 |

The MCU choice is pinned to **ATmega328P** specifically because the firmware already maps ADC counts as `0–1023`, which is a 10-bit converter. Choosing a different MCU later (see §4 alternatives) would mean rescaling that firmware.

---

## 3. Functional Block Overview

```
        +12V automotive in
              |
   [Reverse-polarity P-FET] --- [Input TVS / load-dump clamp] --- [PTC fuse + ferrite]
              |
        +-----+------------------------------+
        |                                     |
   [12V->5V buck (MP1584)]            (raw 12V to voltage divider)
        |                                     |
      +5V rail ---> [5V->3.3V LDO] ---> +3V3 rail (sensors / CAN Vio)
        |
   +----+--------------------------------------------------+
   |          |              |              |               |
 [MCU]   [Analog input   [CAN ctrl     [CAN xceiver    [Status /
ATmega    conditioning]   MCP2515]      MCP2562]        fault LEDs]
328P      (R + RC + clamp)  (SPI)      (CANH/CANL)
   |
 ADC channels:
  - Battery V (30k/10k divider)
  - NTC thermistor divider
  - Throttle analog
  - Brake analog
  - Current sensor (ACS712)
```

---

## 4. Microcontroller (MCU)

**Selected:** `ATmega328P-AU` (TQFP-32)

| Spec | Value | Why it matters here |
| --- | --- | --- |
| ADC | 6–8 ch, 10-bit | Matches existing 0–1023 firmware exactly |
| Logic | 5 V | Reads 0–5 V sensors directly, no level shifting |
| Clock | 16 MHz (external crystal) | Standard Arduino timing; deterministic ADC sampling |
| Toolchain | Arduino / avr-gcc | Reuses the C++ firmware already written |

**Why chosen:** zero firmware rework, abundant documentation, trivially debuggable — ideal for a learning/portfolio node where the *logic* is the point, not exotic silicon.

**Alternatives considered (documented for the portfolio, not selected):**

- **STM32F103C8** — built-in bxCAN peripheral (no MCP2515 needed) and a 12-bit ADC. *Better* long-term part, but it would force a firmware port and rescaling of every ADC mapping. Listed as the **Rev B upgrade path**.
- **ATmega328P on an Arduino Nano module** — fastest to breadboard. Kept as the **prototype option** (see §11).

---

## 5. CAN Interface

The ATmega328P has **no built-in CAN controller**, so CAN is implemented as a controller + transceiver pair — the classic, well-understood Arduino CAN stack.

### 5.1 CAN Controller — `MCP2515` (SPI)
- Talks to the MCU over SPI; handles framing, filtering, and buffering of the `0x100`–`0x105` messages.
- Needs its own clock crystal (8 MHz or 16 MHz) and decoupling.

### 5.2 CAN Transceiver — `MCP2562` (selected over TJA1050 / MCP2551)

| Transceiver | Verdict |
| --- | --- |
| MCP2551 | Older 5 V-only part; no logic-side supply pin |
| TJA1050 | Common on cheap modules, but no `Vio` pin and weaker fault handling |
| **MCP2562** ✅ | Split `Vio` pin (clean 3.3 V/5 V logic interface), driver/thermal protection, automotive-grade |

**Formula E relevance:** on a real car the CAN harness runs the length of the chassis through electrically noisy territory. The transceiver is the part that actually survives bus faults and shorts, so picking a robust one (not the cheapest module part) is the *reliability* decision.

### 5.3 Bus integrity parts
- **120 Ω 1 % termination resistor**, jumper-selectable (only the two physical ends of a CAN bus should be terminated).
- **Common-mode choke** on CANH/CANL — reduces radiated EMI from the bus, which matters near motor/inverter noise.
- **CAN ESD/TVS** (e.g., `PESD1CAN`) across CANH/CANL for transient protection at the connector.

---

## 6. Power Supply & Protection

A 12 V automotive rail is dirty: load dump, reverse-battery during jump-starts, and brownouts during cranking. The power section is mostly *protection*.

| Stage | Selected part | Rationale | Alternative |
| --- | --- | --- | --- |
| Reverse-polarity | P-channel MOSFET (e.g., `DMP3098L`) | Near-zero voltage drop vs a diode → less heat | `SS34` Schottky (simpler, lossier) |
| Input transient | TVS `SMBJ24A` | Clamps load-dump / spikes above ~24 V | `P6KE30A` |
| Overcurrent | Resettable PTC fuse | Self-recovering, no fuse to replace trackside | Glass/blade fuse |
| EMI | Ferrite bead on input | Blocks conducted high-frequency noise | — |
| 12 V → 5 V | Buck regulator `MP1584EN` | High efficiency → little heat at 12 V input | `TPS5430`, or `7805` linear (runs hot) |
| 5 V → 3.3 V | LDO `MCP1700-3302` | Low quiescent current for 3.3 V sensors / CAN `Vio` | `AMS1117-3.3` |
| Decoupling | 100 nF per IC + 10 µF bulk per rail | Stabilizes rails, suppresses switching noise | — |

**Why buck over linear:** a 7805 dropping 12 V → 5 V at even 200 mA dissipates ~1.4 W as heat. In a sealed enclosure on a hot car, that's a thermal liability. A buck converter is the *thermal reliability* decision.

---

## 7. Analog Sensing & Input Conditioning

Each analog channel gets the same protection chain so the ADC never sees something that can damage it — directly implementing the Day 9 "input protection ideas."

**Per-channel conditioning chain:**

```
sensor --> [series R 1k] --> node --> [RC cap 100nF to GND] --> ADC pin
                              |
                         [BAT54S clamp to +5V / GND]
```

| Channel | Sensing element | Selected parts | Notes |
| --- | --- | --- | --- |
| Battery voltage | Resistive divider | R1 = 30 kΩ, R2 = 10 kΩ, **1 % metal film** | ÷4: 12 V → 3.0 V; 1 % keeps the reading accurate |
| Temperature | NTC thermistor | `NTCLE100E3103` (10 kΩ β≈3977) + 10 kΩ 1 % | Divider → ADC → β-equation / Steinhart-Hart in firmware |
| Throttle | Analog 0–5 V (or 0.5–4.5 V) | Conditioning chain only | Sensor is external; node provides protection + filter |
| Brake | Analog 0–5 V | Conditioning chain only | Same as throttle; redundant-plausibility checking lives in fault logic |
| Current | Hall-effect module | `ACS712ELCTR-20A` (analog out) | Non-isolated; converts current → 0–5 V; scaled in firmware |

**Why 1 % resistors on the divider:** at ÷4, a 5 % resistor tolerance can shift the reported pack voltage by a few tenths of a volt — enough to trip or mask an overvoltage fault. Accuracy here is a *safety-logic* decision, not cosmetics.

**Current sensor caveat (documented honestly):** the `ACS712` is non-isolated and the 20 A part is modest. For a real pack-current measurement you'd move to an isolated/higher-range part like `ACS758` or a shunt + isolated amplifier. Logged as a **Rev B** item.

---

## 8. Connectors

Connector choice is where "hobby project" and "motorsports" diverge most.

| Connector | Selected | Why |
| --- | --- | --- |
| Power input | Sealed 2-pos (Deutsch DT / Molex Micro-Fit) | Locking + sealed against vibration and moisture |
| CAN | 4-pos (CANH, CANL, GND, shield) sealed, **or DB9 for bench** | DB9 is the standard CAN debug interface; sealed connector for on-car |
| Sensor I/O | Deutsch DTM series | Vibration-rated, sealed — the FSAE/FE standard for on-car signal harnessing |

**Formula E relevance:** a connector that backs out under vibration is a classic intermittent-fault source. Choosing keyed, locking, sealed connectors is a direct *harness reliability* statement and a good interview talking point.

---

## 9. Indicators, Clock & Debug

| Item | Part | Purpose |
| --- | --- | --- |
| Status LED (green) | LED + 1 kΩ | "Node alive / heartbeat" |
| Fault LED (red) | LED + 1 kΩ | Mirrors the firmware fault state machine |
| MCU clock | 16 MHz crystal + 2× 22 pF | Deterministic timing |
| CAN clock | 8 MHz crystal + caps | MCP2515 reference |
| Programming | 2×3 ICSP header | Flash the ATmega |
| Serial debug | USB-UART (`CH340` / `FT232`) | Feeds the existing `dashboard.py` / `csv_logger.py` over serial |

The USB-UART matters: it's the bridge that lets the Python dashboard and CSV logger from Days 1–9 actually receive data from the physical node.

---

## 10. Selection Summary

| Block | Selected part | One-line reason |
| --- | --- | --- |
| MCU | ATmega328P-AU | Matches existing 10-bit firmware |
| CAN controller | MCP2515 | Adds CAN to a non-CAN MCU |
| CAN transceiver | MCP2562 | Robust, `Vio`-flexible, automotive-grade |
| 12 V → 5 V | MP1584EN buck | Efficient, runs cool |
| 5 V → 3.3 V | MCP1700-3302 LDO | Clean low-noise 3.3 V |
| Reverse protection | P-FET (DMP3098L) | Low-loss reverse-battery block |
| Transient protection | SMBJ24A TVS | Load-dump survival |
| Voltage sense | 30 k / 10 k 1 % | ÷4 to ADC, accurate |
| Temp sense | 10 k NTC | Cheap, well-modeled |
| Current sense | ACS712-20A | Analog, Arduino-friendly |
| Connectors | Deutsch DT/DTM | Vibration-sealed motorsports standard |

---

## 11. Two Build Tiers (so the BOM stays realistic)

- **Tier A — Prototype / breadboard:** Arduino Nano + MCP2515+TJA1050 module + ACS712 module + divider/NTC on a breadboard. Fastest path to validating firmware against real signals.
- **Tier B — Custom PCB (this document's selections):** discrete ATmega328P, MCP2515 + MCP2562, proper power protection, sealed connectors. The portfolio-grade target.

The `bom_draft.md` lists the **Tier B** parts and notes the Tier A module substitutions.

---

## 12. Open Items → carried to later days

- Confirm MCU against existing `hardware/architecture.md` (assumed ATmega328P here).
- Choose final CAN bitrate and update the message-map timing notes.
- Decide current-sense range (20 A proto vs isolated Rev B).
- Schematic capture (Day 11+) to assign real reference designators.
