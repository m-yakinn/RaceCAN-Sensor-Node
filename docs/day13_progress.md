# Day 13 — Progress Log

**Date:** Day 13
**Focus:** Input protection deep-dive
**Deliverables:** `hardware/input_protection.md`, `docs/day13_progress.md`

---

## Summary

Days 11 and 12 placed the protection components on the schematic plan and the floorplan. On Day 13 I wrote the analysis that justifies them. I started from a threat model — nine concrete fault scenarios a vehicle node actually sees, from reverse battery to a chafed sensor wire shorting to +12 V — and then walked every protection element on the board, stating which threat it absorbs, the worst-case numbers that say it survives, and what would fail if it were removed.

Nothing was built or bench-tested. This is design analysis on the planned circuit using datasheet limits and hand calculations, and the document says so explicitly.

---

## What I did today

1. Wrote a nine-entry threat model (T1–T9) covering reverse battery, supply transients, sensor wire shorts to +12 V and to ground, open sensors, ESD, coupled harness noise, CAN bus faults, and board overcurrent.
2. Analyzed the power input chain: the Q1 P-FET reverse-battery block and why it beats a series diode, the F1 PTC trip philosophy, and the D1 SMBJ24A TVS sized against the buck's 28 V input limit, including an honest statement of what a single SMB TVS does not cover.
3. Ran the worst-case numbers for the per-channel chain: a 12 V short into any ADC channel clamps at about 5.3 V and pushes only 6.7 mA through the 1 k series resistor, dissipating 45 mW — survivable indefinitely.
4. Justified the 1 k series value against the ATmega328P's 10 k source-impedance recommendation, and the 100 nF filter cap as a 1.6 kHz low-pass corner that passes every signal the node measures while rejecting harness noise and acting as the anti-aliasing filter.
5. Explained why the BAT54S external clamps exist despite the MCU's internal diodes: lower forward voltage steers fault current away from a 1 mA-rated internal path, and noted the clamp-current-into-rail subtlety with the reasoning for why it is safe at this board's load.
6. Documented the open-sensor case as a firmware-detected fault, connecting the hardware doc to the range and plausibility checks that Day 14 will cover.
7. Covered the CAN-specific protection: why the PESD1CAN's low capacitance matters at 500 kbit/s and what the common-mode choke removes that a TVS cannot.
8. Closed with a summary table mapping every protection element to its threats and its removal consequence.

---

## Open items

- [ ] Confirm Q1's gate-source voltage at maximum input against the DMP3098L rating during KiCad capture.
- [ ] Finalize the F1 PTC trip current once a board current budget is measured.
- [ ] Evaluate an SMCJ-class TVS for Rev B supply environments.
- [ ] Consider a +5V rail clamp if Rev B adds more exposed analog channels.

---

## Next — Day 14 (preview)

Firmware walkthrough: initialization, ADC sampling and filtering, scaling and conversion, the range and plausibility checks that detect the faults the hardware survives, fault-state handling, and telemetry packing. This connects the protection analysis to the code that acts on what the protected inputs report.
