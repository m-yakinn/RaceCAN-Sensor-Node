# Firmware Walkthrough

**Project:** RaceCAN-Sensor-Node — Formula SAE / Formula E–style low-voltage CAN telemetry node
**Stage:** Day 14 (firmware walkthrough — explains the committed template, labels every placeholder and planned change)
**Code under discussion:** `firmware/racecan_firmware_template/racecan_firmware_template.ino`

---

## 1. Purpose of This Document

Days 9 through 13 defined what the hardware does: which signals arrive, how they are scaled and protected, and what survives a fault. Day 14 walks through the firmware that acts on those signals. I go through the committed template in execution order — initialization, the scheduler, sensor acquisition, conversion, fault detection, outputs, and telemetry packing — and for each section I explain what the code does, why it is structured that way, and what the production version will change.

> **Honesty note:** The committed firmware is a documented template, not flight code. CAN transmission is a Serial placeholder, the temperature and current conversions are placeholder math, and there is no digital filtering yet. This document says explicitly which parts are real structure and which parts are stand-ins, and every improvement listed here is planned, not implemented.

---

## 2. Execution Model — Cooperative, Non-Blocking, Two Timing Domains

The firmware uses the standard bare-metal superloop pattern: `setup()` runs once, `loop()` runs forever, and all timing is derived from `millis()` comparisons rather than `delay()`.

```cpp
if (currentTime - previousSensorUpdateTime >= SENSOR_UPDATE_INTERVAL_MS) {
  previousSensorUpdateTime = currentTime;
  readSensors();
  checkFaults();
  updateOutputs();
  // ... telemetry sends ...
}
```

There are two timing domains:

| Task group | Interval | Why this rate |
| --- | --- | --- |
| Sensor read, fault check, outputs, data telemetry | 100 ms (10 Hz) | Fast enough for driver inputs and thermal/electrical trends on a telemetry node; slow enough to leave the bus and CPU mostly idle |
| Heartbeat message | 500 ms (2 Hz) | Liveness signal only; a receiver that misses several consecutive heartbeats can declare the node dead |

The reason `delay()` never appears is that a blocked loop is a deaf node. With subtraction-based `millis()` scheduling, the loop spins freely between deadlines, which is exactly where a future CAN receive handler or watchdog kick will live. The unsigned subtraction also survives the `millis()` rollover at roughly 49.7 days, which matters on a device that stays powered for a whole test day or longer.

One ordering detail worth noticing: within the 100 ms tick, the sequence is read, then check, then act, then transmit. Faults are always evaluated against the freshest sample, and the telemetry sent in a given tick always reflects the fault decision made in that same tick. A receiver never sees a fault flag computed from stale data.

---

## 3. Initialization

`setup()` does four things in order: starts Serial at 115200 baud, configures the external fault input with the internal pull-up, configures the three outputs, and drives all outputs to their safe state before announcing startup and calling `initializeCAN()`.

The external fault input uses `INPUT_PULLUP` with active-low logic (`externalFault = digitalRead(...) == LOW`). This is the standard fail-noisy convention for safety inputs: the line idles high through the pull-up, an external device asserts a fault by pulling it to ground, and a broken wire reads as no-fault. That last property is a known weakness of active-low-with-pullup sensing — an open circuit silently masks the input — and the planned mitigation is to pair it with the heartbeat of whatever node drives that line, so a silent input plus a missing heartbeat is itself a fault.

The shutdown output initializes LOW and is driven HIGH on critical fault, meaning the signal is active-high. I document this deliberately because it is the opposite of how a real FSAE shutdown circuit works: real shutdown loops are normally-closed and break the circuit on fault, so that a cut wire fails safe. For this node, the output models a fault annunciation signal, not a series element of a shutdown loop. If a future revision drives a real shutdown relay, the polarity and the fail-safe analysis both have to be revisited, and I have noted that as an open item rather than pretending the current pin is loop-ready.

`initializeCAN()` is an explicitly labeled placeholder. In the production firmware it becomes the MCP2515 bring-up sequence over SPI: reset, set bit timing for 500 kbit/s with the 16 MHz crystal (the locked Day 10/11 parameters), configure masks and filters, and enter normal mode.

---

## 4. Sensor Acquisition

`readSensors()` performs one `analogRead()` per channel on A0 through A4, matching the prototype pin map in `docs/pin_mapping.md`: throttle, brake, battery voltage, temperature, current. The ATmega328P's ADC returns a 10-bit result, so every raw value is 0–1023 against the 5.0 V reference.

What is deliberately absent right now is digital filtering: each tick uses one raw sample per channel. The hardware already helps — the Day 13 analysis showed the 1 k / 100 nF input RC gives a 1.6 kHz low-pass corner, which acts as the anti-aliasing filter for any sensible firmware sample rate — but single samples are still vulnerable to occasional conversion noise. The planned production change is a small per-channel filter in firmware:

- A median-of-3 to reject single-sample spikes (a glitch from a relay switching nearby should not trip an overcurrent fault), followed by
- An exponential moving average for smoothing trend channels like temperature.

Both are planned, cheap on an ATmega328P, and will be specified alongside the test matrix so the test cases can prove the spike rejection works.

---

## 5. Scaling and Conversion

Each channel has a dedicated conversion function, which keeps the math testable and self-documenting. Channel by channel:

**Throttle and brake — `convertAnalogToPercent()`.** Linear map of 0–1023 to 0–100 percent. This models an ideal ratiometric potentiometer sensor. The production version adds calibrated endpoints (`RAW_MIN`, `RAW_MAX` per pedal) because real pedal sensors never reach the rails, and clamps plus plausibility limits around that calibrated window.

**Battery voltage — `convertAnalogToVoltage()`.** Converts the raw value to pin volts, then multiplies by the divider ratio of 4.0. This is the Day 9 divider carried through: R1 = 30 k over R2 = 10 k divides by 4, so 12.0 V at the harness becomes 3.0 V at the ADC pin, and the firmware multiplies back up. The production change is to replace the round 4.0 with the exact ratio from the chosen 1 % resistors and fold in a measured calibration offset.

**Temperature — `convertAnalogToTemperature()`.** Currently a labeled placeholder that maps 0–1023 linearly to 0–100 °C. A thermistor divider is not linear, so the production version uses the beta equation against the Day 9 divider topology (5 V → fixed resistor → ADC pin → NTC → GND):

```cpp
// Planned production conversion (beta model), not yet in the template
float rNtc = R_FIXED * (float)rawValue / (1023.0 - (float)rawValue);
float tempK = 1.0 / (1.0 / T0_K + log(rNtc / R0) / BETA);
return tempK - 273.15;
```

with `R0`, `T0_K`, and `BETA` from the selected thermistor's datasheet. A lookup table is the fallback if floating-point `log()` proves too heavy in the loop, though at 10 Hz it will not be.

**Current — `convertAnalogToCurrent()`.** Currently a placeholder mapping 0–1023 to 0–20 A. The locked sensor is the ACS712-20A, which is a bidirectional Hall sensor: zero current reads V_CC/2 = 2.5 V, and the 20 A variant moves 100 mV per ampere. The production conversion is therefore offset-and-slope, not a straight ramp:

```cpp
// Planned production conversion for ACS712-20A, not yet in the template
float pinVolts = (rawValue / 1023.0) * 5.0;
return (pinVolts - 2.5) / 0.100;   // amps, negative means reverse current
```

This also changes the fault logic implication: the placeholder can only produce 0 to +20 A, while the real sensor reports direction, so the production overcurrent check compares against the absolute value.

---

## 6. Fault Detection

`checkFaults()` evaluates every flag every tick from the freshest converted values. The thresholds are deliberately two-tier:

| Channel | Warning | Critical fault |
| --- | --- | --- |
| Battery voltage | < 11.0 V | < 10.5 V undervoltage |
| Temperature | > 50.0 °C | > 60.0 °C overtemperature |
| Current | > 12.0 A | > 15.0 A overcurrent |

Warnings aggregate into `anyWarning`; critical faults, the sensor range fault, the external fault pin, and the (currently always-false) communication fault aggregate into `anyCriticalFault`. The two-tier structure exists so the dashboard can show a driver-visible caution before the node escalates to a shutdown-class state — the same normal/warning/fault/shutdown philosophy the BMS simulator branch will formalize as a state machine.

Now the honest part. Three gaps in the current fault logic are known and planned for correction:

**The range fault cannot trigger as written.** `sensorRangeFault` checks whether throttle or brake percent falls outside 0–100, but `convertAnalogToPercent()` mathematically cannot produce a value outside 0–100 from a 10-bit raw input. The check is structurally correct but operates on the wrong variable. The planned fix is to run plausibility windows on the raw ADC values before conversion: a healthy ratiometric sensor on this hardware can never legitimately read near 0 or near 1023, so raw values outside a calibrated window (for example below 20 or above 1000) indicate a short to ground, a short to 5 V or 12 V, or an open sensor. This is the firmware half of Day 13's T3/T4/T5 analysis — the hardware guarantees the pin survives those faults and the signal pins to a detectable rail; the firmware's job is to actually detect it. With the divider topologies on this board, an open sensor floats the pin to a known rail through the remaining fixed resistor, which is exactly what makes the window check work.

**No hysteresis.** A value hovering at a threshold will toggle the fault flag every tick, chattering the LED, the shutdown output, and the fault telemetry. The planned fix is a deadband per threshold: trip at the threshold, clear only after the value retreats past threshold-minus-margin (for example, undervoltage trips below 10.5 V and clears above 10.8 V).

**No latching or persistence.** Faults currently clear themselves the instant the value recovers, and a single noisy sample can assert one. The planned structure — and the explicit subject of the BMS fault state machine day — is N-consecutive-samples to enter a fault, plus latched critical faults that require an explicit reset condition rather than silently self-clearing. On a vehicle, a fault that disappears on its own is a fault you can no longer diagnose.

`communicationFault` is hardwired false because the placeholder CAN layer cannot fail. Once the MCP2515 driver is real, this flag picks up transmit-error and bus-off detection from the controller's error registers.

---

## 7. Outputs and System State

`updateOutputs()` turns the status LED on (firmware-alive indicator), and on any critical fault drives the fault LED and the shutdown output high together. The mapping from flags to a single reportable state lives in `getSystemStateCode()`: 0 normal, 1 warning, 2 fault. That one-byte code rides in the heartbeat, which means a receiver gets the node's overall health for free at 2 Hz without parsing the full fault message.

A planned refinement is to make the status LED blink rather than sit solid — a solid LED cannot distinguish healthy firmware from firmware frozen with the pin high, while a 1 Hz blink is a visible heartbeat. The same reasoning eventually adds the AVR watchdog timer: enabled in `setup()`, kicked once per loop pass, so a hung loop causes a reset instead of a silent dead node. Both are deferred to the build-phase firmware pass.

---

## 8. Telemetry Packing

The CAN message map matches the locked ID block 0x100–0x105:

| ID | Message | Payload layout (bytes) |
| --- | --- | --- |
| 0x100 | Heartbeat | [0] alive=1, [1] state code, [2:3] uptime low/high, [4:7] reserved |
| 0x101 | Voltage | [0:1] volts × 100 (int16 LE), [2] warning, [3] fault, [4:7] reserved |
| 0x102 | Temperature | [0:1] °C × 100 (int16 LE), [2] warning, [3] fault, [4:7] reserved |
| 0x103 | Driver inputs | [0:1] throttle % × 100, [2:3] brake % × 100, [4] range fault, [5:7] reserved |
| 0x104 | Current | [0:1] amps × 100 (int16 LE), [2] warning, [3] fault, [4:7] reserved |
| 0x105 | Faults | one flag per byte: V warn, UV fault, T warn, OT fault, I warn, OC fault, range, external/comm |

The scaling convention is fixed-point ×100 packed little-endian into two bytes via `lowByte()`/`highByte()`. This is the standard CAN idiom: floats are wasteful and non-portable on a bus, while volts × 100 in an int16 gives 0.01 V resolution over ±327 V of range — far more than needed, with two bytes per signal. The receiving side (the Python dashboard) divides by 100 and gets the value back exactly.

Two packing details worth recording honestly. First, the heartbeat uptime field truncates: `millis() / 1000` is packed through `lowByte`/`highByte`, so the counter wraps at 65 536 seconds (about 18.2 hours). That is acceptable for a liveness counter whose only job is to visibly change between messages, and the limit is now documented. Second, every message uses DLC 8 with explicit reserved bytes even when fewer would do; for a learning artifact I prefer fixed, fully specified frames over variable-length frames, and the reserved bytes are where Day 15's message map spec can grow fields without renumbering IDs.

`sendCANMessage()` itself is the placeholder boundary: it prints the ID and bytes over Serial in a fixed format instead of touching hardware. This is deliberate — the Serial output is the same frame content a real MCP2515 would transmit, which is what lets the Python simulator and dashboard consume realistic telemetry without hardware. The production replacement is a single function swap: load the ID and data into the MCP2515 transmit buffer over SPI and request transmission. Nothing upstream changes, which is the payoff of routing every message through one choke point.

---

## 9. Known Divergences From the Locked Hardware Design

The template predates the Day 10–12 hardware decisions, so three reconciliations are on record for the build-phase firmware pass:

1. **Pin conflicts.** The template drives shutdown, fault LED, and status LED on D11/D12/D13, which are the SPI MOSI/MISO/SCK pins the MCP2515 needs. `docs/pin_mapping.md` already documents the planned relocation (shutdown → D4, fault LED → D5, status LED → D6, CS → D10, INT → D3). The template intentionally keeps the simple pin map because it runs without CAN hardware; the relocation lands when the MCP2515 driver does.
2. **CAN interrupt versus polling.** The MCP2515 INT line is planned to PD2/D3, but whether receive handling uses the interrupt or polls the controller's status register is still the open item carried since Day 11. The transmit-only telemetry in this template works either way, so the decision is deferred to when receive functionality is specified.
3. **Target naming.** The template reads as Arduino Uno/Nano (A0–A4, D-numbers) while the locked schematic is a bare ATmega328P-AU. These are the same silicon and the same ports; the build-phase pass will add a pin-definition header that maps the named signals to physical port pins so the firmware and the netlist use one vocabulary.

---

## 10. Summary — Template Today, Production Plan

| Area | In the committed template | Planned production change |
| --- | --- | --- |
| Scheduling | Non-blocking millis() superloop, 10 Hz / 2 Hz | Unchanged; add watchdog kick |
| ADC | Single sample per tick | Median-of-3 + EMA per channel |
| Throttle/brake | Ideal 0–1023 → 0–100 % | Calibrated endpoints + raw plausibility windows |
| Voltage | ×4.0 divider constant | Exact ratio from 1 % resistors + calibration |
| Temperature | Linear placeholder | Beta-equation thermistor conversion |
| Current | Linear 0–20 A placeholder | ACS712 offset/slope, bidirectional, abs() fault check |
| Fault logic | Instantaneous thresholds | Hysteresis, N-sample persistence, latched criticals |
| Range fault | Checks converted percent (cannot trip) | Raw ADC window checks (detects T3/T4/T5) |
| Comm fault | Hardwired false | MCP2515 error-register monitoring |
| CAN | Serial placeholder, frames fully formatted | MCP2515 SPI driver, same frame content |
| Pins | Uno-style, D11–13 outputs | Relocated map per pin_mapping.md, port-pin header |

The structural skeleton — the scheduler, the read/check/act/transmit ordering, the per-channel conversion functions, the single CAN choke point, and the message map — survives into production unchanged. That was the point of writing the template this way.
