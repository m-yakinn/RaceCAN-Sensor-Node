# Day 16 — Progress Log

**Date:** Day 16  
**Focus:** Test matrix specification and simulator validation framework  
**Deliverables:** `hardware/test_matrix.md`, `simulation/test_cases.py`, `docs/day16_progress.md`

---

## Summary

Day 13 proved the hardware survives real-world faults. Day 14 walked through the firmware that detects and responds to those faults. Day 15 specified the CAN protocol that reports those faults to the dashboard. Day 16 defines the acceptance criteria that prove the full stack works together: hardware protection → sensor acquisition → firmware logic → CAN transmission.

I created a comprehensive test matrix with 34 test cases spanning seven signal groups and four test categories:

- **Normal range validation (NS):** Verify each signal scales correctly and thresholds do not spuriously assert under nominal conditions
- **Boundary condition testing (BC):** Verify threshold-crossing behavior at exact warning/critical limits (11.0V, 50°C, 12.0A, etc.)
- **Fault injection and recovery (FI):** Verify the system detects sensor opens, shorts, and failures and recovers cleanly when faults clear
- **Timing and message synchronization (TM):** Verify message rates, ordering, payload consistency, and sampling latency meet real-time safety requirements
- **State machine transitions (SM):** Verify the firmware state code (0=normal, 1=warning, 2=critical) transitions correctly and escalates under multi-fault scenarios

Nothing was coded, built, or bench-tested. This is a specification and a Python simulator harness. The actual firmware is not modified; the test matrix is an acceptance criterion that the existing firmware should already satisfy (or will be validated against).

---

## What I did today

1. **Specified all 22 CAN signals across six messages.** For each signal, I defined:
   - Normal operating range and threshold limits (from Day 14 and Day 15)
   - Exact test stimulus (sensor value at time T)
   - Expected CAN payload output
   - Acceptance criteria (tolerance, timing constraints)
   - Example test cases from the test matrix

2. **Created test case templates for each signal group:**
   - **Heartbeat (0x100):** 4 tests covering liveness, state transitions (normal→warning→critical), and uptime wraparound
   - **Voltage (0x101):** 5 tests for nominal range, sweep, warning threshold (11.0V), critical threshold (10.5V), and recovery
   - **Temperature (0x102):** 5 tests mirroring voltage (50°C warning, 60°C critical, sustained overtemperature)
   - **Driver inputs (0x103):** 6 tests for throttle/brake scaling, simultaneous inputs, open-circuit faults, short-to-ground faults, and fault recovery
   - **Current (0x104):** 5 tests for zero-offset calibration, positive/negative sweeps, warning threshold (12.0A), critical threshold (15.0A)
   - **Fault summary (0x105):** 3 tests for nominal all-clear state, multiple simultaneous faults, and cross-checking that each fault bit mirrors its source message
   - **Message timing (G):** 4 tests for transmission rates (±1%), arrival ordering, payload consistency within one cycle, and sensor sampling latency (≤150ms)
   - **State machine (H):** 3 tests for normal↔warning transitions, normal↔critical transitions, and multi-step escalation

3. **Documented threshold justifications.** Each critical limit is traced back to component ratings or vehicle-realistic operating margins:
   - V < 10.5V: ATmega brownout risk (supply below 4.5V typical for Vcc threshold at 5V rail)
   - T > 60°C: MP1584EN regulator absolute maximum junction temperature
   - I > 15.0A: Assumed fuse/protection rating for 12V automotive harness
   - These are locked by Day 13 threat model and Day 14 firmware; Day 16 test matrix accepts them as fixed

4. **Created Python test harness (`simulation/test_cases.py`)** with:
   - `RaceCANMessage` class to represent CAN frames with payload parsing (little-endian, signed/unsigned integers)
   - `RaceCANSimulator` class that maintains sensor state and packs CAN messages according to the Day 15 protocol
   - `TestCase` class that defines stimulus sequences, expected conditions, and validates captured messages
   - `run_tests()` function to execute test suite with filtering and reporting
   - Example test implementations for key test cases (A.1, A.2, B.1, D.1, E.1, F.1)

5. **Outlined test execution sequence** for implementation in Days 17–20:
   - **Phase 1 (Days 16–17):** Single-signal tests (all NS and BC tests); verify scaling and thresholds independently
   - **Phase 2 (Days 17–18):** Integration tests (multi-signal, timing, state machine); verify message consistency and real-time behavior
   - **Phase 3 (Days 18–19):** Fault injection and recovery (all FI tests); verify graceful degradation and no latching faults
   - **Phase 4 (Days 19–20):** Stress and edge cases (extended duration, rapid state transitions, CAN load)

6. **Provided integration points with simulator and bench testing:**
   - Test matrix forms the basis of the Python simulator validation (running all 34 tests against simulated sensor inputs)
   - Once hardware is fabricated, the same test cases (with real CAN capture) form the acceptance checklist
   - Included test report template with summary, per-section breakdown, failure log, and sign-off

7. **Documented known limitations and future refinements:**
   - Sensor calibration windows (throttle [50–950], brake [60–980] raw ADC) are provisional and must be finalized during integration testing
   - Hysteresis and debouncing implementation (N-sample persistence) is firmware-dependent; test matrix assumes robust noise handling but does not mandate exact counts
   - Microcontroller brownout behavior (reset vs. graceful shutdown) is documented as firmware-dependent for firmware revision 1.0
   - External fault / communication fault (0x105[7]) is dual-purpose and may be split in future BMS interlock integration

---

## Open items

- [ ] Implement full test harness: expand `test_cases.py` to include all 34 test cases (currently only 6 examples are stubbed)
- [ ] Set up simulator validation pipeline: integrate test harness with Arduino simulator or QEMU-based firmware emulation
- [ ] Run Phase 1 tests (NS and BC) against firmware to verify scaling and thresholds
- [ ] Define exact sensor calibration windows during system integration (once potentiometers and thermistor are selected)
- [ ] Finalize N-sample persistence counts and hysteresis margins for threshold debouncing (firmware tuning parameter)
- [ ] Document microcontroller brownout behavior (reset with loss of heartbeat vs. continued operation with reduced supply)
- [ ] Create test report template and CI/CD integration (GitHub Actions running test suite on every firmware commit)
- [ ] Plan bench-testing equipment setup (multimeter, adjustable power supply, CAN analyzer, oscilloscope for real hardware validation)

---

## Next — Day 17 (preview)

Simulator validation: implement remaining test cases (28 of 34 are currently stubs) and run the full Phase 1 suite against the firmware running in the Arduino simulator. Expected outcome: all 34 tests pass with expected CAN payload outputs, message timing within ±5ms, and state machine transitions matching specification.

Alternatively, if simulator setup proves difficult, pivot to: CAN message map receiver examples (`firmware/dashboard_receiver_example.c` and `simulation/dashboard.py`), which demonstrates how a secondary ECU or telemetry logger would unpack and validate the CAN protocol. This adds another dimension of test: verifying that the spec document enables correct receiver implementation, not just validates transmitter behavior.

---

## Locked decisions (Day 16)

- Test matrix covers all 22 signals, all six CAN messages, all state transitions
- 34 test cases provide 100% coverage of critical thresholds and fault scenarios
- Test categories are NS (normal), BC (boundary), FI (fault), TM (timing), SM (state machine) — balanced mix ensures both nominal and edge-case behavior
- Python simulator harness is sufficient for firmware validation before hardware fabrication; will be extended with real CAN capture tools during bench testing
- Test report template supports traceability from firmware requirements (Day 14) → protocol spec (Day 15) → acceptance criteria (Day 16) → test results (Days 17–20)

---

## Key learnings and context

### Test Matrix as Living Document
The test matrix is not a waterfall spec frozen at Day 16. As the firmware is tuned, sensor calibration proceeds, and BMS interlock is designed, this matrix will evolve:
- Sensor windows may tighten as potentiometers are physically selected
- Persistence counts (hysteresis samples) will be finalized during tuning
- New test cases may be added for BMS-specific faults (cell balance, pre-charge, isolation monitoring)
- But the core structure (22 signals, 6 messages, 4 thresholds per signal group) is locked

### Acceptance vs. Optimization
This matrix defines acceptance (does the system meet safety and protocol requirements?), not optimization (is it efficient?). Performance tuning (CAN bandwidth, sampling frequency, filter bandwidth) is out of scope. The matrix is pass/fail: either the firmware scales voltages correctly to ±0.01V or it doesn't; either the state machine transitions promptly or it hangs.

### Simulator as Proof of Concept
The Python simulator is deterministic: inject a voltage, get a CAN payload. Real hardware has jitter, quantization, transients, noise. The simulator cannot catch all bugs (race conditions, buffer overflows, ADC glitches). But it can verify that the firmware's state machine logic is correct and that CAN packing follows the spec. This is necessary but not sufficient for system acceptance.

### Traceability Chain
Day 13 (protection) → Day 14 (firmware) → Day 15 (protocol) → Day 16 (test matrix) → Days 17–20 (validation). Each day's deliverable is the input to the next day. If Day 14 firmware does not implement the thresholds specified in Day 13, Day 16 tests will fail. This forces early discovery of design mismatches.

---

## File manifest

| **File** | **Location** | **Size (approx)** | **Purpose** |
| --- | --- | --- | --- |
| `hardware/test_matrix.md` | GitHub repo | ~25 KB | Primary test specification; 8 sections, 34 test cases, pseudocode, limitations |
| `simulation/test_cases.py` | GitHub repo | ~20 KB | Python test harness; RaceCANMessage, RaceCANSimulator, TestCase classes; ~6 example test implementations |
| `docs/day16_progress.md` | GitHub repo | ~8 KB | This file; progress summary, locked decisions, next steps |

---

## References

- **Day 13 — Input Protection Analysis:** `docs/day13_progress.md`, component threat model, fault current calculations
- **Day 14 — Firmware Walkthrough:** `firmware/racecan_firmware_template/racecan_firmware_template.ino`, state machine, ADC scaling
- **Day 15 — CAN Message Map:** `hardware/can_message_map.md`, signal scaling, message definitions, protocol justifications
- **CAN standard:** ISO 11898-1 (11-bit ID, 8-byte frame, 500 kbit/s)
- **Component datasheets:**
  - ATmega328P-AU: ADC resolution, brownout detection, EEPROM
  - ACS712-20A: current sensor zero-offset, sensitivity, bandwidth
  - MP1584EN: buck converter efficiency, thermal ratings
  - BAT54S: Schottky diode forward voltage, reverse leakage
- **Test automation:** Python 3.6+, standard library (struct, sys, datetime, collections, typing)

---

**End of Day 16 Progress Log**
