# Day 14 — Progress Log

**Date:** Day 14
**Focus:** Firmware walkthrough
**Deliverables:** `firmware/firmware_walkthrough.md`, `docs/day14_progress.md`

---

## Summary

Day 13 proved the hardware survives the faults a vehicle harness delivers. Day 14 walks through the firmware that acts on what the protected inputs report. I went through the committed template in execution order — scheduler, initialization, acquisition, conversion, fault detection, outputs, telemetry packing — explaining what each section does and why, and labeling every placeholder and every planned production change explicitly.

The walkthrough is documentation of code that exists in this repository, plus clearly marked planned changes. Nothing new was claimed as implemented; the planned thermistor and ACS712 conversions appear as labeled future code, not as committed behavior.

---

## What I did today

1. Documented the cooperative non-blocking execution model: two timing domains (10 Hz sensors/telemetry, 2 Hz heartbeat), rollover-safe millis() subtraction, and the read-check-act-transmit ordering that keeps fault flags consistent with the data they ride alongside.
2. Walked initialization, including the active-low external fault input and its open-wire blind spot, and the active-high shutdown output with an honest note that a real FSAE shutdown loop is normally-closed and this pin models annunciation, not a loop element.
3. Explained each conversion function, carried the Day 9 numbers through (divide-by-4 voltage divider), and wrote the planned production conversions for the thermistor (beta equation) and the ACS712-20A (2.5 V offset, 100 mV/A, bidirectional), both labeled as planned.
4. Audited the fault logic and recorded three known gaps with their fixes: the range fault that cannot trigger because it checks converted percent instead of raw ADC windows, the missing hysteresis, and the missing latching/persistence — connecting the raw-window fix directly to threats T3/T4/T5 from the Day 13 analysis.
5. Documented the telemetry packing convention (fixed-point ×100, int16 little-endian, DLC 8 with reserved bytes) and the full 0x100–0x105 payload map as currently coded, including the 18.2-hour heartbeat uptime wrap.
6. Recorded the three known divergences from the locked hardware design: the D11–D13 SPI pin conflict and its planned relocation, the open CAN_INT interrupt-versus-poll decision, and the Uno-style naming versus the bare ATmega328P-AU target.
7. Closed with a template-versus-production table showing which structure survives unchanged and which placeholders get replaced in the build phase.

---

## Open items

- [ ] Decide MCP2515 receive handling: PD2 interrupt versus status-register polling (carried since Day 11).
- [ ] Add the pin-definition header mapping signal names to ATmega328P port pins during the build-phase firmware pass.
- [ ] Specify exact plausibility window values (raw ADC min/max per channel) when the test matrix is written.
- [ ] Define hysteresis margins and N-sample persistence counts per threshold alongside the test matrix.
- [ ] Rename `docs/day_12_progress.md` to `docs/day12_progress.md` to match the log naming pattern.

---

## Next — Day 15 (preview)

CAN message map specification: formalize the 0x100–0x105 frames as a standalone protocol document — signal names, byte offsets, scaling factors, units, ranges, transmission rates, and the receiver-side decoding rules the dashboard implements. The walkthrough documented what the code packs today; Day 15 turns that into the specification the code is held against.
