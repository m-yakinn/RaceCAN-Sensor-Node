# Test Matrix Specification

**Project:** RaceCAN-Sensor-Node — Formula SAE / Formula E–style low-voltage CAN telemetry node  
**Firmware reference:** `firmware/racecan_firmware_template/racecan_firmware_template.ino` (Day 14 walkthrough)  
**CAN protocol reference:** `hardware/can_message_map.md` (Day 15 specification)  
**Date:** Day 16  
**Status:** Acceptance criteria for firmware + simulation validation; basis for future bench-test checklist

---

## 1. Scope and Purpose

This test matrix enumerates acceptance criteria for the RaceCAN node across all operating modes:
- **Normal operation:** All signals in healthy ranges, no faults
- **Warning conditions:** Single-fault injection, threshold crossing, early shutdown cues
- **Critical faults:** Sensor failures, hardware failures, shutdown-triggering scenarios
- **Timing and reliability:** Message transmission rates, no gaps, no duplicates, state machine coherence

The test matrix covers **22 individual signals** across **six CAN messages** (0x100–0x105), plus **message-level timing** and **state machine transitions**. All tests are specified in terms of input stimulus (simulated sensor values, fault injection) and expected output (CAN message payload and state codes).

---

## 2. Test Case Organization

### By Signal Type

| **Signal Group** | **Signal Count** | **Messages** | **Key Thresholds** |
| --- | --- | --- | --- |
| Heartbeat | 3 (alive, state, uptime) | 0x100 | State transitions (0→1→2) |
| Voltage | 3 (value, warning, critical) | 0x101 | 11.0 V (warn), 10.5 V (crit) |
| Temperature | 3 (value, warning, critical) | 0x102 | 50 °C (warn), 60 °C (crit) |
| Driver inputs | 3 (throttle, brake, range fault) | 0x103 | [50–950] throttle, [60–980] brake (raw ADC) |
| Current | 3 (value, warning, critical) | 0x104 | 12.0 A (warn), 15.0 A (crit) |
| Fault summary | 8 (mirrors + external) | 0x105 | All critical thresholds |

### By Test Category

1. **Normal range validation** (NS = Normal Single-signal)
2. **Boundary condition testing** (BC = Boundary Crossing)
3. **Fault injection and recovery** (FI = Fault Injection)
4. **Timing and synchronization** (TM = Timing/Message validation)
5. **State machine transitions** (SM = State Machine)

---

## 3. Test Case Specification

### **Section A: Heartbeat (0x100) — 4 Test Cases**

#### **A.1 — NS-HB-001: Normal heartbeat liveness (Alive=1, State=0)**

| **Aspect** | **Specification** |
| --- | --- |
| **Stimulus** | Firmware running, all sensors nominal (V=12.0V, T=25°C, I=0A, throttle=0%, brake=0%) |
| **Duration** | 5 seconds (10 heartbeat frames at 500 ms interval) |
| **Expected output** | 0x100: [0x01, 0x00, uptime_0, uptime_1, 0x00, 0x00, 0x00, 0x00] where uptime increments by 1 every second |
| **Acceptance criteria** | Alive flag is always 1; state code is always 0; uptime increments monotonically; no gaps >600 ms between frames |
| **Purpose** | Verify baseline heartbeat transmission and uptime counter accuracy |

#### **A.2 — BC-HB-002: State transition to warning (State=1)**

| **Aspect** | **Specification** |
| --- | --- |
| **Stimulus** | Start at nominal state (0x100[1]=0). At t=1s, inject battery voltage = 10.8V (crosses 11.0V warning threshold). Maintain for 2s. Then recover to 12.0V. |
| **Duration** | 5 seconds total |
| **Expected output** | Frames 1–2: State=0. Frame 3 onwards (at voltage < 11.0V): State=1. Frame recovery (after V returns to 12.0V): State returns to 0 after ~500ms (one message cycle latency). |
| **Acceptance criteria** | State code correctly reflects warning mode; transition is prompt (within one message interval); recovery is clean with no oscillation |
| **Purpose** | Verify state machine responds to warning threshold crossing |

#### **A.3 — BC-HB-003: State transition to critical (State=2)**

| **Aspect** | **Specification** |
| --- | --- |
| **Stimulus** | Start at nominal state (0x100[1]=0). At t=1s, inject battery voltage = 10.3V (crosses 10.5V critical threshold). Hold for 2s. |
| **Duration** | 5 seconds total |
| **Expected output** | Frames 1–2: State=0. Frame 3 onwards: State=2. System enters critical fault mode; all fault summary bits in 0x105 are set to 1 (or at least the voltage critical bit 0x105[1]=1). Uptime counter continues to increment. |
| **Acceptance criteria** | State transitions to 2 on critical voltage; all downstream fault bits assert correctly; state remains 2 until voltage recovers above 10.5V AND system reset or explicit recovery is confirmed |
| **Purpose** | Verify critical fault detection and state machine behavior under shutdown condition |

#### **A.4 — TM-HB-004: Heartbeat timing and uptime wraparound**

| **Aspect** | **Specification** |
| --- | --- |
| **Stimulus** | Simulate firmware runtime of 65530 seconds (uptime counter near 16-bit max). Transmit heartbeat frames. |
| **Duration** | Measure 10 frames (5 seconds) |
| **Expected output** | Uptime field [2:3] reads 0xEA 0xFF (little-endian 65530). After wraparound at 65535s, the next heartbeat shows 0x00 0x00. |
| **Acceptance criteria** | Uptime wraps correctly at 65535s (~18.2 hours); receiver can track multiple wraps by watching discontinuities; no undefined behavior in firmware during wraparound |
| **Purpose** | Verify long-lived session robustness and wraparound handling |

---

### **Section B: Voltage Telemetry (0x101) — 5 Test Cases**

#### **B.1 — NS-V-001: Normal voltage range (12.0V nominal)**

| **Aspect** | **Specification** |
| --- | --- |
| **Stimulus** | Battery voltage = 12.0V (stable). All other sensors nominal. |
| **Duration** | 2 seconds (20 messages at 100ms interval) |
| **Expected output** | 0x101: [0xB0 0x04, 0x00, 0x00, ...] where bytes [0:1] = 0x04B0 (little-endian 1200 = 12.00V). Voltage warning [2]=0, critical [3]=0. |
| **Acceptance criteria** | Transmitted voltage matches input to within ±0.01V (scaling resolution); warning and critical flags are 0; message interval is consistent 100±5ms |
| **Purpose** | Verify nominal voltage transmission and scaling |

#### **B.2 — NS-V-002: Voltage range sweep (10.5V to 14.4V)**

| **Aspect** | **Specification** |
| --- | --- |
| **Stimulus** | Ramp battery voltage from 10.5V to 14.4V in 10 steps over 2 seconds (0.19V/step, ~200ms/step). Then ramp back down. |
| **Duration** | 4 seconds |
| **Expected output** | 0x101 payload [0:1] sweeps from 1050 to 1440 and back. Warning flag [2] stays 0 throughout (no value crosses 11.0V threshold from above). Critical flag [3] stays 0 (no value below 10.5V). |
| **Acceptance criteria** | All voltages are transmitted correctly; no threshold flags assert during sweep; scaling is linear and continuous |
| **Purpose** | Verify ADC-to-CAN scaling across full operating range |

#### **B.3 — BC-V-003: Voltage warning threshold (11.0V exact)**

| **Aspect** | **Specification** |
| --- | --- |
| **Stimulus** | Start at 12.0V. At t=1s, drop to exactly 11.00V and hold for 1s. Then drop to 10.99V and hold. |
| **Duration** | 3 seconds |
| **Expected output** | Frames 1–10 (t=0–1s): voltage warning flag = 0. At t=1s, one frame may show boundary behavior (firmware samples at 50ms intervals; exact threshold crossing may appear on next message cycle). From t=1s+100ms: voltage warning flag = 1. When voltage = 10.99V: voltage critical flag = 1. |
| **Acceptance criteria** | Warning flag asserts at or just after crossing 11.0V (within one message cycle); critical flag does not assert spuriously when V=11.00V; hysteresis is appropriate (no chattering if actual noise ±0.05V near threshold) |
| **Purpose** | Verify warning threshold implementation and hysteresis |

#### **B.4 — BC-V-004: Voltage critical threshold (10.5V exact)**

| **Aspect** | **Specification** |
| --- | --- |
| **Stimulus** | Start at 11.5V. At t=1s, drop to exactly 10.50V. Hold for 1s. At t=2s, drop to 10.49V. |
| **Duration** | 3 seconds |
| **Expected output** | Frames 1–10: critical flag = 0. At t=1s+100ms (one message cycle): critical flag = 1. State code in 0x100 changes to 2 (critical fault). System enters shutdown-pending state. 0x105[1] (voltage critical mirror) asserts. When V drops to 10.49V: all signals may become invalid as microcontroller approaches brownout (firmware behavior TBD: may freeze, reset, or transmit garbage). |
| **Acceptance criteria** | Critical flag asserts at/after crossing 10.5V; state machine enters fault mode; receiver detects liveness loss if firmware resets; no undefined CAN traffic |
| **Purpose** | Verify critical threshold and microcontroller brownout behavior |

#### **B.5 — FI-V-005: Voltage recovery from critical fault**

| **Aspect** | **Specification** |
| --- | --- |
|
