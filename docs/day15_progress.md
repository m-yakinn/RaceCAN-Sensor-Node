# Day 15 — Progress Log

**Date:** Day 15  
**Focus:** CAN message map specification  
**Deliverables:** `hardware/can_message_map.md`, `docs/day15_progress.md`

---

## Summary

Day 13 proved the hardware survives the faults a vehicle harness delivers. Day 14 walked through the firmware that acts on those protected inputs. Day 15 formalized the CAN protocol that carries those signals to the vehicle dashboard.

I took the six-message telemetry set (0x100–0x105) documented in the firmware walkthrough and elevated it into a standalone protocol specification: signal names, byte offsets, scaling factors, units, valid ranges, transmission rates, fault thresholds, and receiver-side decoding rules. The spec reads as a protocol document that a receiver engineer could implement from, with pseudocode examples in both Python and C, a field summary table for quick reference, trade-off justifications for design choices, and reserved-byte roadmap for future expansions.

Nothing was coded, built, or bench-tested. This is documentation and specification of the protocol the Day 14 firmware implements and transmits.

---

## What I did today

1. **Specified the six-frame message set.** Locked the 0x100–0x105 ID block with one frame per major signal group: heartbeat, voltage, temperature, driver inputs (throttle/brake), current, and fault summary.

2. **Documented scaling across all signal types.** Every multi-byte integer field is little-endian; every analog signal uses fixed-point ×100 for 0.01 unit resolution. Chose this over floating-point for determinism, compactness, and alignment with automotive CAN convention.

3. **Specified bit-level message layouts.** For each of the six messages, I documented every byte, its type, range, units, and semantic meaning. Example: 0x101 [0:1] = battery voltage as int16 LE in volts×100, [2] = warning flag (V < 11.0 V), [3] = critical fault (V < 10.5 V).

4. **Justified every fault threshold.** The thresholds came from the firmware walkthrough (Day 14) which came from a combination of component ratings and vehicle-realistic operating margins. This spec carries those forward with explicit context: undervoltage 10.5 V is ATmega brownout risk, overtemperature 60 °C is component derating limit, etc.

5. **Recorded the sensor range fault mechanism.** The firmware detects open sensors and shorts by checking raw ADC window plausibility. This spec explains why: a healthy ratiometric sensor on 5 V reference with the hardware divider topology cannot legitimately read near rail voltages, so values outside a calibrated window (example: throttle [50–950] raw) indicate hardware fault.

6. **Provided receiver implementation examples.** Two pseudocode blocks: Python dashboard receiver and C embedded receiver, showing how to unpack little-endian fields, scale fixed-point back to physical units, and use the heartbeat for node-loss detection.

7. **Created a field summary table.** One row per signal (22 fields total), with message ID, byte offset, type, scaling, range, and unit — a quick cheat sheet for receiver code generation.

8. **Justified design trade-offs explicitly.** Why fixed-point over floats (determinism, space), why fixed 8-byte payloads (simplicity, forward compatibility), why heartbeat separate from data (tunable rates), why 0x105 mirrors faults from 0x101–0x104 (redundancy and quick parse).

9. **Documented reserved-byte roadmap.** Every message reserves bytes [4:7] for future expansion with example candidates: firmware version, multi-sensor temps, LDO currents, mode buttons, etc. All future fields will maintain LE scaling for backward-compatible parsing.

10. **Closed with version history and references.** Version 1.0 is Day 15 initial spec; Day 16+ refinements will be incremented. References point to the Day 14 firmware walkthrough (what packs these), Day 13 protection (what set the thresholds), and a forward pointer to the test matrix (coming Day 16+).

---

## Open items

- [ ] Finalize sensor plausibility windows (throttle raw min/max, brake raw min/max) once system calibration data is available.
- [ ] Specify exact hysteresis margins and N-sample persistence counts for each threshold (currently stated as "planned" in firmware, will be locked during test matrix work).
- [ ] Decide whether external fault input should remain dual-purpose with communication fault or split into separate bytes once BMS interlock integration is clear (Day 16+).
- [ ] Create receiver implementation examples: `firmware/dashboard_receiver_example.c` (for a secondary ECU) and `simulation/dashboard.py` (for telemetry logging).
- [ ] Plan the test matrix for Day 16: enumerate test cases for each threshold, each signal range, each fault condition, and the expected message output.

---

## Next — Day 16 (preview)

Test matrix specification: enumerate test cases that prove the hardware and firmware work together correctly. For each of the 22 signals in the CAN protocol, define:
- Normal-range test cases (throttle 0%, 50%, 100%; battery 10.5–14.4 V; temperature −10 to +70 °C)
- Boundary / threshold cases (voltage exactly at 11.0 V warning, at 10.5 V critical, etc.)
- Fault and recovery cases (sensor shorted to ground, shorted to 12 V, open wire — and the raw ADC window that detects it)
- Timing cases (rapid current spikes, temperature ramps, pedal jitter)
- Message timing validation (all frames arrive at expected rates, no gaps, no duplicates)

This becomes the acceptance criteria for the software simulator and, later, the bench-test checklist when hardware is fabricated.

---

**End of Day 15 Progress Log**
