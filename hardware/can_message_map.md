# CAN Message Map Specification

**Project:** RaceCAN-Sensor-Node — Formula SAE / Formula E–style low-voltage CAN telemetry node  
**Firmware reference:** `firmware/racecan_firmware_template/racecan_firmware_template.ino` (Day 14 walkthrough)  
**Date:** Day 15  
**Status:** Protocol specification for the locked message set 0x100–0x105 at 500 kbit/s, 8-byte frames

---

## 1. Overview

The RaceCAN node transmits six CAN frames to a vehicle dashboard or telemetry receiver. Every frame uses 8-byte payloads (DLC = 8) with reserved bytes for future expansion. All multi-byte fields are little-endian. Transmission rates are fixed: data messages every 100 ms (10 Hz), heartbeat every 500 ms (2 Hz).

| **ID** | **Name** | **Interval** | **Purpose** |
| --- | --- | --- | --- |
| 0x100 | Heartbeat | 500 ms | Liveness signal, node state code, uptime counter |
| 0x101 | Voltage telemetry | 100 ms | Battery voltage, warning, critical undervoltage fault |
| 0x102 | Temperature telemetry | 100 ms | Ambient / component temperature, warning, critical overtemperature fault |
| 0x103 | Driver inputs | 100 ms | Throttle and brake pedal positions, sensor range fault |
| 0x104 | Current telemetry | 100 ms | Pack current (bidirectional), warning, critical overcurrent fault |
| 0x105 | Fault summary | 100 ms | One byte per fault condition for dashboard quick-parse |

---

## 2. Signal Scaling Convention

All multi-byte integer fields are **little-endian** and packed using standard CAN integer methods (`lowByte()` / `highByte()` in firmware).

### Voltage and current signals use **fixed-point ×100**:

- **Voltage example:** 12.34 volts is transmitted as 1234 (an int16 LE = 0xD2 0x04 in bytes [0:1])
- **Current example:** 5.67 amps is transmitted as 567 (an int16 LE)
- **Temperature example:** 45.20 °C is transmitted as 4520 (an int16 LE)

This gives 0.01-unit resolution and avoids floating-point encoding. The receiving side divides the received value by 100 to recover the physical quantity.

### Percentage signals use **fixed-point ×100**:

- **Throttle example:** 67.5 percent is transmitted as 6750 (int16 LE)

This allows sub-percent resolution if calibration improves over time.

---

## 3. Message Definitions

### **0x100 — Heartbeat (sent every 500 ms)**

| **Byte** | **Field** | **Type** | **Range** | **Notes** |
| --- | --- | --- | --- | --- |
| [0] | Alive flag | uint8 | 0 or 1 | Always 1 when transmitting; receiver uses message presence as liveness. |
| [1] | State code | uint8 | 0–2 | **0** = normal, **1** = warning, **2** = critical fault / shutdown mode |
| [2:3] | Uptime (seconds) | uint16 LE | 0–65535 | `millis() / 1000`, wraps at ~18.2 hours. Receiver plots continuous uptime as (received × 1000) ms. |
| [4:7] | Reserved | — | — | All zeros for now; available for future heartbeat extensions (e.g., firmware version, hardware variant). |

**Decoding pseudocode (Python receiver):**
```python
alive = data[0]
state_code = data[1]
uptime_sec = int.from_bytes(data[2:4], byteorder='little')
state_name = {0: 'normal', 1: 'warning', 2: 'fault'}[state_code]
```

---

### **0x101 — Voltage Telemetry (sent every 100 ms)**

| **Byte** | **Field** | **Type** | **Range** | **Units** | **Notes** |
| --- | --- | --- | --- | --- | --- |
| [0:1] | Battery voltage | int16 LE | 0–3270 | 0.01 V (transmit `volts × 100`) | Divider-scaled harness voltage. Normal range 10.5–14.4 V. |
| [2] | Voltage warning | uint8 | 0 or 1 | Binary | Asserts when battery drops below 11.0 V (caution, not critical). |
| [3] | Voltage critical fault | uint8 | 0 or 1 | Binary | Asserts when battery drops below 10.5 V (system shutdown threshold). |
| [4:7] | Reserved | — | — | — | All zeros; available for future voltage fields (e.g., supply rail ripple, LDO health). |

**Valid ranges and thresholds:**
- **Normal operation:** 11.0 V ≤ V ≤ 14.4 V
- **Warning threshold:** V < 11.0 V (e.g., charging system failure, load surge)
- **Critical threshold:** V < 10.5 V (microcontroller brownout risk; node initiates safe shutdown)
- **Over-voltage:** This node's input protection (SMBJ24A TVS at 28 V) handles transients above 14.4 V without fault; no separate OV field needed in current design

**Decoding pseudocode (Python receiver):**
```python
raw_voltage = int.from_bytes(data[0:2], byteorder='little')
voltage_v = raw_voltage / 100.0
v_warn = data[2]
v_crit = data[3]
if v_crit: print(f"VOLTAGE CRITICAL: {voltage_v:.2f} V < 10.5 V")
```

---

### **0x102 — Temperature Telemetry (sent every 100 ms)**

| **Byte** | **Field** | **Type** | **Range** | **Units** | **Notes** |
| --- | --- | --- | --- | --- | --- |
| [0:1] | Temperature | int16 LE | −4000 to +10000 | 0.01 °C (transmit `temp × 100`) | Thermistor or thermal sensor reading. Negative for below-freezing operation (e.g., high-altitude). |
| [2] | Temperature warning | uint8 | 0 or 1 | Binary | Asserts when T > 50 °C (component caution, e.g., regulator junction approaching derating limit). |
| [3] | Temperature critical fault | uint8 | 0 or 1 | Binary | Asserts when T > 60 °C (thermal shutdown, e.g., component failure risk). |
| [4:7] | Reserved | — | — | — | All zeros; available for multi-sensor temperature (e.g., thermistor + regulator + MCU junction). |

**Valid ranges and thresholds:**
- **Normal operation:** −20 °C ≤ T ≤ 50 °C
- **Warning threshold:** T > 50 °C (regulator thermal derating begins; advise reduced load or cooling)
- **Critical threshold:** T > 60 °C (component absolute maximum risk; node initiates shutdown)
- **Over-temperature scenario:** e.g., regulator in a poorly ventilated enclosure under sustained 20 A load

**Decoding pseudocode (Python receiver):**
```python
raw_temp = int.from_bytes(data[0:2], byteorder='little', signed=True)
temp_c = raw_temp / 100.0
t_warn = data[2]
t_crit = data[3]
if t_crit: print(f"TEMPERATURE CRITICAL: {temp_c:.2f} °C > 60 °C")
```

---

### **0x103 — Driver Inputs (sent every 100 ms)**

| **Byte** | **Field** | **Type** | **Range** | **Units** | **Notes** |
| --- | --- | --- | --- | --- | --- |
| [0:1] | Throttle position | uint16 LE | 0–10000 | 0.01 % (transmit `percent × 100`) | ADC-sampled potentiometer analog input. 0 = fully closed, 10000 = fully open (100%). |
| [2:3] | Brake position | uint16 LE | 0–10000 | 0.01 % (transmit `percent × 100`) | ADC-sampled brake pressure or pedal analog input. 0 = no braking, 10000 = full braking (100%). |
| [4] | Sensor range fault | uint8 | 0 or 1 | Binary | Asserts if throttle or brake raw ADC value is outside the calibrated valid window (indicates open sensor, short to rail, or ADC failure). See *Sensor Range Fault* section below. |
| [5:7] | Reserved | — | — | — | All zeros; available for clutch position, gear selection, or steering angle. |

**Sensor range fault details:**

The firmware samples throttle and brake as 10-bit raw ADC values (0–1023). A healthy ratiometric sensor on a 5.0 V reference with the divider topology in the hardware design cannot legitimately read near the rails. Plausibility windows are defined during system calibration:

- Example: throttle valid window [50–950] raw ADC
- Example: brake valid window [60–980] raw ADC

If either value is outside its window, `sensorRangeFault = 1`. This detects:
- Open sensor → floats toward a predictable rail through the fixed resistor
- Short to ground → raw ADC = 0
- Short to 5 V or 12 V → raw ADC = 1023
- ADC failure (stuck value, noise) → reads outside normal operation

**Decoding pseudocode (Python receiver):**
```python
throttle_raw = int.from_bytes(data[0:2], byteorder='little')
brake_raw = int.from_bytes(data[2:4], byteorder='little')
throttle_pct = throttle_raw / 100.0
brake_pct = brake_raw / 100.0
range_fault = data[4]
if range_fault: print(f"SENSOR RANGE FAULT: T={throttle_pct:.2f}%, B={brake_pct:.2f}%")
```

---

### **0x104 — Current Telemetry (sent every 100 ms)**

| **Byte** | **Field** | **Type** | **Range** | **Units** | **Notes** |
| --- | --- | --- | --- | --- | --- |
| [0:1] | Pack current | int16 LE | −2000 to +2000 | 0.01 A (transmit `amps × 100`) | Hall-effect current sensor output (ACS712-20A). Positive = forward (charging or discharge convention TBD), negative = reverse. |
| [2] | Current warning | uint8 | 0 or 1 | Binary | Asserts when \|current\| > 12.0 A (sustained high current, advise load reduction or cooling). |
| [3] | Current critical fault | uint8 | 0 or 1 | Binary | Asserts when \|current\| > 15.0 A (overcurrent shutdown, possible fault detection or pack-side behavior). |
| [4:7] | Reserved | — | — | — | All zeros; available for series-cell current sense, BMS bypass current, or load-specific shunts. |

**Valid ranges and thresholds:**
- **Normal operation:** −12 A ≤ I ≤ +12 A
- **Warning threshold:** \|I\| > 12 A (sustained load beyond typical cruise; may cause regulator thermal stress or wire heating)
- **Critical threshold:** \|I\| > 15 A (short, catastrophic load, or sensor fault; triggers node shutdown and pack-level protection investigation)
- **Sensor characteristics (ACS712-20A):** zero-current output = 2.5 V, sensitivity = 100 mV/A, ratiometric, bidirectional

**Decoding pseudocode (Python receiver):**
```python
raw_current = int.from_bytes(data[0:2], byteorder='little', signed=True)
current_a = raw_current / 100.0
i_warn = data[2]
i_crit = data[3]
if i_crit: print(f"OVERCURRENT CRITICAL: |{current_a:.2f}| A > 15.0 A")
```

---

### **0x105 — Fault Summary (sent every 100 ms)**

| **Byte** | **Field** | **Type** | **Value** | **Meaning** |
| --- | --- | --- | --- | --- |
| [0] | Voltage warning | uint8 | 0 or 1 | Battery voltage < 11.0 V (mirrors 0x101[2]) |
| [1] | Voltage critical | uint8 | 0 or 1 | Battery voltage < 10.5 V (mirrors 0x101[3]) |
| [2] | Temperature warning | uint8 | 0 or 1 | Temperature > 50 °C (mirrors 0x102[2]) |
| [3] | Temperature critical | uint8 | 0 or 1 | Temperature > 60 °C (mirrors 0x102[3]) |
| [4] | Current warning | uint8 | 0 or 1 | \|Current\| > 12 A (mirrors 0x104[2]) |
| [5] | Current critical | uint8 | 0 or 1 | \|Current\| > 15 A (mirrors 0x104[3]) |
| [6] | Sensor range fault | uint8 | 0 or 1 | Throttle or brake ADC out of window (mirrors 0x103[4]) |
| [7] | External fault / communication fault | uint8 | 0 or 1 | External fault input asserted OR CAN transmit error detected (dual-purpose; refinement planned for Day 16+). |

**Purpose:** Allows a receiver to quickly check the overall system health from a single 8-byte frame without parsing all six messages. A dashboard can light a single "ANY FAULT" LED based on 0x105[1], 0x105[3], 0x105[5], or 0x105[6] without processing voltage, temperature, and current separately.

**Decoding pseudocode (Python receiver):**
```python
faults = {
    'voltage_warn': data[0],
    'voltage_crit': data[1],
    'temperature_warn': data[2],
    'temperature_crit': data[3],
    'current_warn': data[4],
    'current_crit': data[5],
    'sensor_range': data[6],
    'external_comm': data[7],
}
any_critical = data[1] or data[3] or data[5] or data[6]
if any_critical: print("SYSTEM CRITICAL FAULT")
```

---

## 4. Transmission Rates and Timing

| **Message** | **ID** | **Rate** | **Interval (ms)** | **Per-minute count** |
| --- | --- | --- | --- | --- |
| Heartbeat | 0x100 | 2 Hz | 500 | 120 |
| Voltage | 0x101 | 10 Hz | 100 | 600 |
| Temperature | 0x102 | 10 Hz | 100 | 600 |
| Driver inputs | 0x103 | 10 Hz | 100 | 600 |
| Current | 0x104 | 10 Hz | 100 | 600 |
| Fault summary | 0x105 | 10 Hz | 100 | 600 |

**Bus loading calculation:**
- Each message is 8 bytes of payload + CAN overhead (~64 bits per message including headers and spacing)
- Total: 5 × 10 Hz × 64 bits + 1 × 2 Hz × 64 bits = 3200 + 128 = 3328 bits/sec
- **500 kbit/s bus utilization:** 3328 / 500000 ≈ 0.66% — comfortably idle, room for additional nodes, logging, or redundancy

---

## 5. Field Summary Table (Receiver Implementation Reference)

This table is a quick reference for implementing a CAN-to-struct decoder:

| **Message ID** | **Signal name** | **Bytes** | **Type** | **Scaling** | **Min** | **Max** | **Unit** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0x100 | Alive | [0] | uint8 | — | 0 | 1 | Binary |
| 0x100 | State code | [1] | uint8 | — | 0 | 2 | Index |
| 0x100 | Uptime | [2:3] | uint16 LE | ÷1 | 0 | 65535 | Seconds |
| 0x101 | Battery voltage | [0:1] | int16 LE | ÷100 | 0 | 327.67 | Volts |
| 0x101 | Voltage warning | [2] | uint8 | — | 0 | 1 | Binary |
| 0x101 | Voltage critical | [3] | uint8 | — | 0 | 1 | Binary |
| 0x102 | Temperature | [0:1] | int16 LE | ÷100 | −40 | 100 | Celsius |
| 0x102 | Temp warning | [2] | uint8 | — | 0 | 1 | Binary |
| 0x102 | Temp critical | [3] | uint8 | — | 0 | 1 | Binary |
| 0x103 | Throttle % | [0:1] | uint16 LE | ÷100 | 0 | 100 | Percent |
| 0x103 | Brake % | [2:3] | uint16 LE | ÷100 | 0 | 100 | Percent |
| 0x103 | Sensor range fault | [4] | uint8 | — | 0 | 1 | Binary |
| 0x104 | Pack current | [0:1] | int16 LE | ÷100 | −20 | +20 | Amperes |
| 0x104 | Current warning | [2] | uint8 | — | 0 | 1 | Binary |
| 0x104 | Current critical | [3] | uint8 | — | 0 | 1 | Binary |
| 0x105 | V warn | [0] | uint8 | — | 0 | 1 | Binary |
| 0x105 | V crit | [1] | uint8 | — | 0 | 1 | Binary |
| 0x105 | T warn | [2] | uint8 | — | 0 | 1 | Binary |
| 0x105 | T crit | [3] | uint8 | — | 0 | 1 | Binary |
| 0x105 | I warn | [4] | uint8 | — | 0 | 1 | Binary |
| 0x105 | I crit | [5] | uint8 | — | 0 | 1 | Binary |
| 0x105 | Range fault | [6] | uint8 | — | 0 | 1 | Binary |
| 0x105 | Ext fault / comm fault | [7] | uint8 | — | 0 | 1 | Binary |

---

## 6. Receiver Implementation Notes

### Python Dashboard Receiver Example

A receiver implementing this spec should:

1. **Filter for the node's ID range.** The RaceCAN node uses 0x100–0x105. A multi-node vehicle may use 0x100–0x10F for RaceCAN, 0x200–0x20F for BMS, 0x300–0x30F for motor controller, etc.
2. **Unpack fixed-point fields by dividing by 100.** For all voltage, temperature, and current fields: `display_value = raw_int16 / 100.0`
3. **Treat binary flags as state machines, not noise.** Once a critical fault asserts (0x101[3], 0x102[3], 0x104[3]), it stays asserted until the node resets or recovers and transmits a clear. A receiver should log the timestamp and treat clearing as a separate event.
4. **Use the heartbeat to detect node loss.** If three consecutive heartbeats are missed (>1.5 seconds with 500 ms interval), declare the node dead and set all telemetry to "unknown" instead of holding stale values.
5. **Validate message timing in the dashboard log.** Sudden gaps in 10 Hz messages (0x101–0x105) indicate firmware freezing or bus congestion. Log the gap and alert the driver.

### C/Embedded Receiver Example (Receiver Node Firmware)

A receiving node on the same CAN bus can parse these frames directly in an interrupt handler:

```c
// Pseudocode structure for receiving RaceCAN telemetry
void process_racecan_message(uint16_t can_id, uint8_t *data, uint8_t dlc) {
    switch (can_id) {
        case 0x100: {
            uint16_t uptime_sec = (data[3] << 8) | data[2];  // LE unpack
            uint8_t state = data[1];
            // Update dashboard state code and uptime display
            break;
        }
        case 0x101: {
            int16_t raw_voltage = (data[1] << 8) | data[0];  // LE unpack
            float voltage = raw_voltage / 100.0;
            if (data[3]) shutdown_pin = HIGH;  // Voltage critical
            break;
        }
        // ... handle 0x102, 0x103, 0x104, 0x105 similarly
    }
}
```

---

## 7. Future Expansions (Reserved Bytes)

Every message reserves bytes [4:7] (or specific bytes if already used) for future fields. Planned expansions:

- **0x100 (heartbeat):** Firmware version, hardware variant, module serial number
- **0x101 (voltage):** LDO rail voltage, supply ripple, regulator junction temperature
- **0x102 (temperature):** Multi-sensor temps (regulator junction, thermistor, MCU die), humidity if added
- **0x103 (driver inputs):** Clutch position, shift selector, mode buttons
- **0x104 (current):** Per-rail shunt currents (5V, 3.3V separately), battery bypass current
- **0x105 (fault summary):** Communication/watchdog status, driver-requested shutdown, BMS interlock state

All extensions will maintain little-endian scaling and byte alignment for backward-compatible receiver parsing.

---

## 8. Design Decisions and Trade-offs

### Why fixed-point ×100 instead of floats?

**Float (IEEE 754, 4 bytes):** Portable, precise, but non-deterministic on embedded receivers and wastes space for signals needing only 0.01 resolution.  
**Fixed-point ×100 (2 bytes):** Deterministic across platforms, compact, sufficient resolution (0.01 V, 0.01 A, 0.01 °C are practice-relevant), and aligns with CAN convention in automotive.

### Why 8-byte fixed-length payloads?

**Variable length (DLC 1–8):** Saves bus bandwidth if only a few signals change per tick.  
**Fixed length (DLC 8):** All messages are byte-aligned, reserved bytes document future growth, and receiver code is simpler (no branch on DLC).

### Why heartbeat separate from data messages?

**Single unified heartbeat:** Proves the entire system is alive; dashboard uses it as primary liveness timeout.  
**Data at 10 Hz:** Separating allows tuning: heartbeat can drop to 1 Hz on long hauls if bandwidth becomes limited, while driver inputs stay fresh at 10 Hz.

### Why mirror fault flags in 0x105 if they're already in 0x101–0x104?

**Redundancy:** A receiver checking only 0x105 gets system health in one parse. A detailed receiver uses 0x101–0x104 for thresholds and trends.  
**Robustness:** One corrupted frame (0x101) does not leave 0x105 stale; both are refreshed at the same rate.  
**Simplicity:** Dashboard firmware can AND 0x105[1,3,5,6] for a single "critical fault" signal without conditional logic.

---

## 9. Version History

| **Date** | **Day** | **Version** | **Changes** |
| --- | --- | --- | --- |
| — | Day 15 | 1.0 | Initial specification: 0x100–0x105, all signals, scaling, receiver notes |
| — | Day 16+ | 1.1+ | (Planned: refinement after test matrix feedback, BMS interlock integration) |

---

## References

- **Day 14 firmware walkthrough:** `firmware/firmware_walkthrough.md` — explains the code that packs these messages
- **Day 10–11 hardware locking:** `hardware/component_selection.md`, `hardware/schematic_planning.md` — locked signal set
- **Day 13 protection analysis:** `hardware/input_protection.md` — fault scenarios that shaped these thresholds
- **Planned test matrix:** `test/test_matrix.md` (Day 16 or later) — will enumerate test cases for each threshold and signal range
- **Dashboard receiver reference:** `firmware/dashboard_receiver_example.c` or `simulation/dashboard.py` (future builds)

---

**End of CAN Message Map Specification**
