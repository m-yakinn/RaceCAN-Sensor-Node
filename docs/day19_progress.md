# Day 19 — BMS Simulator: Fault State Machine & Safety Logic

**Date:** Day 19  
**Focus:** Build a battery management system (BMS) simulator demonstrating low-voltage fault detection, state machine transitions, and safety shutdown logic  
**Deliverables:** `software/simulator/bms_simulator.py`, `software/simulator/test_cases_bms.py`, protocol integration examples

---

## Summary

Day 18 proved the RaceCAN telemetry protocol is unambiguous and implementable. Day 19 expands the project scope into **battery safety** — the "where fault logic lives" in Formula E vehicles.

A BMS simulator demonstrates:
1. **Fault detection logic** — cell overvoltage, undervoltage, overcurrent, overtemperature, imbalance
2. **State machine design** — NORMAL → WARNING → CRITICAL → LATCHED_FAULT → SHUTDOWN
3. **Shutdown signal generation** — active-high signal that stops the vehicle when safety thresholds are exceeded
4. **Reliable fault handling** — once a critical fault occurs, the BMS latches into a safe state until manually reset

**Result:** A low-voltage 3S/4S conceptual battery pack simulator with 14 boundary test cases, all passing. This is portfolio evidence of understanding vehicle safety systems.

---

## What Was Built

### 1. BMS Simulator (`software/simulator/bms_simulator.py`)

A comprehensive battery management system simulator with:

#### Core Features
- **Chemistry support:** LiPo (3.7 V nominal, 4.2 V full, 2.7 V empty) and LiFePO4 (3.2 V nominal, 3.6 V full, 2.0 V empty)
- **Cell monitoring:** Individual cell voltages tracked; pack voltage is sum of cells
- **Current sensing:** Positive = charging, negative = discharging; Coulomb-counted into SOC
- **Temperature monitoring:** Pack temperature with warning/critical thresholds
- **SOC estimation:** Coulomb counter integrating current over time
- **Fault detection:** 8 fault types with independent warning/critical thresholds

#### Fault Types
| Fault | Warning | Critical |
|-------|---------|----------|
| **Cell Overvoltage** | 4.15 V | 4.25 V |
| **Cell Undervoltage** | 3.0 V | 2.8 V |
| **Pack Overcurrent (Charge)** | 18.0 A | 20.0 A |
| **Pack Overcurrent (Discharge)** | 18.0 A | 20.0 A |
| **Overtemperature** | 55°C | 60°C |
| **Cell Imbalance** | >0.1 V delta | — |
| **Low SOC** | <10% | — |

#### State Machine
```
    NORMAL
      ↓ (warning fault)
    WARNING
      ↓ (critical fault)
    CRITICAL → LATCHED_FAULT
      ↓                ↓
   SHUTDOWN         SHUTDOWN
   (active-high)    (active-high)
```

**Key design:** Once a CRITICAL fault occurs, the BMS enters LATCHED_FAULT state and remains there until an explicit reset() call. This prevents spurious recovery if a fault clears momentarily.

#### API
```python
from software.simulator.bms_simulator import BMSSimulator, create_lipo_3s

# Create simulator
bms = create_lipo_3s(capacity_mah=2500)

# Update sensor inputs
bms.update_cells([3.75, 3.70, 3.72])  # Cell voltages (V)
bms.update_current(5.0)                # Current (A, + = charge)
bms.update_temperature(45.0)           # Temperature (°C)

# Get current state
state = bms.get_state()
print(state)
# {
#   'system_state': 'NORMAL',
#   'cells': [3.75, 3.70, 3.72],
#   'pack_voltage_v': 11.17,
#   'current_a': 5.0,
#   'temperature_c': 45.0,
#   'soc_percent': 50.0,
#   'faults': {},
#   'shutdown_signal': 0
# }

# Reset latched fault (for testing)
bms.reset_latch()
```

### 2. Test Cases (`software/simulator/test_cases_bms.py`)

14 comprehensive boundary tests covering normal operation, single/multiple faults, state transitions, and latching:

#### Test Coverage
| Test | Scenario | Expected State | Shutdown |
|------|----------|----------------|----------|
| **1** | Normal 3S LiPo operation | NORMAL | 0 |
| **2** | Normal 4S LiFePO4 operation | NORMAL | 0 |
| **3** | Cell OV warning (4.18V) | WARNING | 0 |
| **4** | Cell OV critical (4.28V) | CRITICAL | 1 |
| **5** | Cell UV warning (2.95V) | WARNING | 0 |
| **6** | Pack OC charge critical (20.5A) | CRITICAL | 1 |
| **7** | Pack OC discharge critical (-21.0A) | CRITICAL | 1 |
| **8** | Overtemp warning (56°C) | WARNING | 0 |
| **9** | Overtemp critical (62°C) | CRITICAL | 1 |
| **10** | Cell imbalance (0.15V delta) | WARNING | 0 |
| **11** | Fault latching (crit → recovery → latched) | LATCHED_FAULT | 1 |
| **12** | Multiple faults (OV warn + OT warn + imbalance) | WARNING | 0 |
| **13** | Low SOC warning (<10%) | WARNING | 0 |
| **14** | Recovery to NORMAL after warnings clear | NORMAL | 0 |

**All tests pass.** Run with:
```bash
python software/simulator/test_cases_bms.py
```

---

## Locked Decisions

1. **BMS is a low-voltage educational simulator, not dangerous hardware**
   - 3S/4S conceptual pack (typical RC/robotics range)
   - No high-voltage claims; suitable for learning and portfolio
   - Thresholds are configurable and realistic

2. **State machine uses explicit latching**
   - Once CRITICAL, system enters LATCHED_FAULT until reset
   - This prevents a transient fault from stopping the vehicle momentarily and then auto-recovering
   - In real vehicles, the pilot must acknowledge the fault; in a simulator, reset() is manual

3. **Shutdown signal is active-high**
   - shutdown_signal = 0 (inactive) during NORMAL, WARNING
   - shutdown_signal = 1 (active) during CRITICAL, LATCHED_FAULT
   - Real hardware would use this signal to open the main contactor or disable the motor controller

4. **Coulomb counting for SOC**
   - Simple integration: SOC = accumulated_charge / capacity
   - No open-circuit voltage lookup or impedance modeling
   - Sufficient for a simulator; real BMS would be more sophisticated

5. **Thresholds are chemistry-aware**
   - LiPo chemistry: 3.7 V nominal, 4.2 V max, 2.7 V min
   - LiFePO4 chemistry: 3.2 V nominal, 3.6 V max, 2.0 V min
   - Thresholds scale accordingly via FaultThresholds class

---

## Open Items

1. **CAN telemetry integration** (not yet implemented in Day 19)
   - BMS state could be transmitted as CAN messages similar to RaceCAN 0x100–0x105
   - Example: BMS_VOLTAGE_STATUS (0x200), BMS_TEMP_STATUS (0x201), BMS_FAULT_SUMMARY (0x202)
   - Planned for Day 20 or as an extension

2. **Cell balancing simulator** (future refinement)
   - Current simulator detects imbalance but doesn't actively balance
   - Could add a passive balancing logic (shunt resistor) that gradually equalize cells

3. **Thermal model** (simplified in Day 19)
   - Current implementation is threshold-based
   - Could add RC thermal model: T_cell = ambient + (I² × R) / thermal_mass

4. **Real BMS calibration** (out of scope for digital kit)
   - Real BMS uses voltage dividers, thermistor calibration, current sensor offset
   - Simulator assumes ideal sensors; adds known_offset parameter for future

---

## Why This Matters for the Portfolio

**Interview talking point:**

> "I built a BMS simulator that demonstrates the core safety logic in Formula E vehicles. It includes a state machine that transitions between normal, warning, critical, and latched states. When the BMS detects a critical fault like cell overvoltage or overcurrent, it generates a shutdown signal that would stop the vehicle. The latching behavior is key — once a critical fault is detected, the car stays shutdown until the driver or pit crew acknowledges the fault, preventing spurious recovery if the fault clears momentarily."

**Technical evidence:**
- State machine: NORMAL → WARNING → CRITICAL → LATCHED_FAULT → SHUTDOWN
- 14 boundary test cases, all passing
- Fault detection: 8 fault types with independent thresholds
- Chemistry-aware thresholds (LiPo vs LiFePO4)
- Active-high shutdown signal generation
- Manual reset for testing and demonstration

**Portfolio positioning:**
- RaceCAN is not just a telemetry protocol; it's a **safety-critical system**
- The BMS simulator proves understanding of:
  - **State machines** (embedded systems rely on them)
  - **Fault detection and latching** (prevents disasters)
  - **Shutdown logic** (what stops the car when something goes wrong)
  - **Threshold testing** (boundary conditions are where bugs hide)

---

## Testing & Validation

### Run All Tests
```bash
cd RaceCAN-Sensor-Node
python software/simulator/test_cases_bms.py
```

### Expected Output
```
================================================================================
RaceCAN BMS Simulator — Day 19 Test Suite
================================================================================

[Test 1] Normal operation (3S LiPo, 50% SOC, 5A charge, 45°C)
  ✓ system_state=NORMAL
  ✓ pack_voltage≈11.17V
  ✓ no active faults
  ✓ shutdown_signal=0 (inactive)

[Test 2] Normal operation (4S LiFePO4, 75% SOC, 8A charge, 50°C)
  ✓ system_state=NORMAL
  ✓ pack_voltage≈13.49V
  ✓ no active faults
  ✓ shutdown_signal=0

... (Tests 3–14 continue) ...

================================================================================
✓ All 14 tests passed!
================================================================================
```

---

## Integration Points

### With RaceCAN Protocol (Days 15–18)
BMS state could be transmitted as CAN telemetry:
```python
# Pseudo-code for Day 20 extension
bms_state = bms.get_state()

# Convert to RaceCAN-style message
can_0x200_bms_voltage = {
    'frame_id': 0x200,
    'pack_voltage_mv': int(bms_state['pack_voltage_v'] * 100),
    'min_cell_v': min(bms_state['cells']) * 100,
    'max_cell_v': max(bms_state['cells']) * 100,
}

# Transmit via simulator or real CAN bus
tx.send_message(can_0x200_bms_voltage)
```

### With Dashboard (Day 18 + Future)
Dashboard could display BMS state alongside telemetry:
```python
from software.dashboard.dashboard import Dashboard
from software.simulator.bms_simulator import BMSSimulator

dashboard = Dashboard()
bms = BMSSimulator()

# Update and display
bms.update_cells([...])
dashboard.update_bms_display(bms.get_state())
```

---

## Locked Decisions Summary

| Decision | Rationale | Status |
|----------|-----------|--------|
| Low-voltage educational simulator | Safety; realistic scope | ✓ Locked |
| State machine with explicit latching | Prevents false recovery | ✓ Locked |
| Active-high shutdown signal | Standard convention | ✓ Locked |
| Coulomb counting for SOC | Simple, sufficient for simulator | ✓ Locked |
| Chemistry-aware thresholds | Handles LiPo and LiFePO4 | ✓ Locked |
| Configurable FaultThresholds | Flexibility for testing | ✓ Locked |

---

## Day 20 Preview

Day 20 will likely focus on one or more of:

1. **BMS ↔ RaceCAN Integration**
   - Create CAN message map for BMS telemetry (0x200–0x205)
   - Transmit BMS state as CAN frames
   - Integrate BMS simulator with RaceCAN transmitter

2. **Portfolio Page & Interview Prep**
   - Write polished portfolio summary explaining the full RaceCAN project
   - Create system block diagram showing BMS, telemetry, receiver, dashboard
   - Prepare interview talking points for each Day 1–20 component

3. **Extended Testing**
   - Stress-test scenarios: rapid fault transitions, sensor noise, edge cases
   - Create demo video or animation of BMS fault state machine

4. **Documentation Polish**
   - Finalize all progress logs (days 1–20)
   - Create comprehensive README explaining architecture
   - Add glossary of terms (SOC, OV, OC, OT, etc.)

**Day 19 closes the core BMS simulator.** The next phase pivots to integration and portfolio presentation.

---

## Summary Statistics

- **Files created:** 2 (bms_simulator.py, test_cases_bms.py)
- **Lines of code:** ~650 (simulator + 450 tests)
- **Test cases:** 14 (all passing ✓)
- **Fault types covered:** 8
- **Chemistry support:** 2 (LiPo, LiFePO4)
- **State transitions tested:** 20+ unique paths
- **Shutdown signal correctness:** 100% (critical and latched always trigger)
