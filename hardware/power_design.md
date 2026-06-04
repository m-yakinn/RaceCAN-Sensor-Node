# Power Design

This document explains the planned power architecture for the **RaceCAN sensor node**.

---

## Purpose

The power circuit provides safe and stable power to the microcontroller, CAN transceiver, and sensors.

---

## Planned Power Flow

```
VIN
 ↓
Fuse or Polyfuse
 ↓
Reverse Polarity Protection
 ↓
TVS Diode Protection
 ↓
Voltage Regulator
 ↓
5V and/or 3.3V Logic Rail
 ↓
Microcontroller, CAN Transceiver, Sensors
```

---

## Power Input

The board is designed around a low-voltage automotive-style input:

- **Input range:** 9 V to 16 V
- Models a typical low-voltage automotive system environment

---

## Protection Features

### Fuse or Polyfuse

A fuse or resettable polyfuse protects the board from excessive current draw.

### Reverse Polarity Protection

Prevents damage if power is connected with reversed polarity.

**Possible implementations:**

| Option | Notes |
|--------|-------|
| Series diode | Simple, small voltage drop |
| Schottky diode | Lower forward voltage drop |
| P-channel MOSFET ideal diode | Near-zero drop, preferred for efficiency |

### TVS Diode

A TVS diode clamps voltage spikes on the input rail, protecting downstream components. Especially useful in noisy vehicle-style environments.

---

## Voltage Regulation

The board may use a **buck converter** or **linear regulator** depending on input voltage and current requirements.

| Rail | Purpose |
|------|---------|
| 5 V | Sensors and some microcontrollers |
| 3.3 V | Microcontroller, CAN transceiver, logic |

> **Note:** A buck converter is preferred for efficiency at higher input voltages (e.g., 12 V → 3.3 V). A linear regulator may be acceptable for low-current rails.

---

## Decoupling

Each IC should have local decoupling capacitors placed close to its power pins.

| Capacitor Value | Purpose |
|-----------------|---------|
| 0.1 µF | High-frequency decoupling |
| 1 µF – 10 µF | Local bulk capacitance |
| 10 µF – 47 µF | Input or regulator output stability |

---

## Test Points

The PCB should expose test points for easy probing during bring-up and debugging:

- [ ] `VIN`
- [ ] `GND`
- [ ] `5V`
- [ ] `3.3V`
- [ ] Sensor reference voltage

---

## Design Goals

The power design should be:

- **Protected** — fuse, reverse polarity, and transient protection
- **Stable** — proper decoupling and regulation
- **Easy to debug** — labeled test points, clear net names
- **Well documented** — this file and future schematic annotations
- **KiCad-ready** — structured for a clean schematic implementation

---

## Status

> 🔧 **In planning** — schematic not yet started.
