# Day 10 — Progress Log

**Date:** Day 10
**Focus:** Component selection and draft bill of materials
**Deliverables:** `hardware/component_selection.md`, `hardware/bom_draft.md`, `docs/day10_progress.md`

---

## Summary

Day 9 finished the *architecture* — the sensor inputs, the conversion math, and the protection concepts. Day 10 turns that architecture into a concrete (still paper-only) parts list: a specific MCU, a CAN controller + transceiver pair, a protected 12 V power section, per-channel analog input conditioning, and motorsports-grade connectors. The goal was not just to list parts, but to **justify each one** the way you'd defend it in a design review or an FE team interview.

No parts were purchased and no PCB was fabricated — this is a documented design exercise.

---

## What was done today

1. Established **design anchors** carried from Days 1–9 (5 V logic, 10-bit ADC, 12 V supply, single CAN channel, the 30 k/10 k divider).
2. Pinned the **MCU to ATmega328P** because the existing firmware maps ADC counts as 0–1023 (a 10-bit converter). Documented STM32F103 as a Rev B upgrade path.
3. Selected the **CAN stack**: MCP2515 controller + MCP2562 transceiver, with termination, common-mode choke, and bus TVS — and wrote down why MCP2562 beats the cheaper TJA1050/MCP2551.
4. Designed the **power section as mostly protection**: reverse-polarity P-FET, load-dump TVS, PTC fuse, buck (not linear) for 12 V → 5 V, plus a 3.3 V LDO.
5. Defined a repeatable **per-channel analog conditioning chain** (series R → RC filter → Schottky clamp) implementing Day 9's protection ideas.
6. Chose **sealed Deutsch connectors** for vibration/moisture resistance.
7. Wrote the **draft BOM** with example MPNs, packages, indicative quantities, and Tier A (breadboard) substitutions.

---

## Key decisions & rationale

| Decision | Chosen | Why | Rejected alternative |
| --- | --- | --- | --- |
| MCU | ATmega328P | No firmware rework; matches 10-bit ADC mapping | STM32F103 (forces firmware port) |
| CAN transceiver | MCP2562 | `Vio` pin + better fault protection | TJA1050 (cheap module part) |
| 12 V → 5 V | MP1584 buck | Stays cool vs ~1.4 W in a 7805 | 7805 linear |
| Reverse protection | P-FET | Near-zero drop | Schottky diode (lossier) |
| Divider resistors | 1 % metal film | Tolerance directly affects fault thresholds | 5 % (cheaper, less accurate) |
| Connectors | Sealed Deutsch | Survive vibration; standard on-car practice | Header pins |

---

## Formula E / FSAE relevance

- **Load-dump TVS + reverse-polarity FET:** the 12 V rail on a car is hostile (transients, jump-start reversals). Protecting against it is a core LV-electronics competency.
- **CAN termination + common-mode choke:** bus reliability near motor/inverter noise is exactly what a telemetry node has to survive.
- **1 % sense resistors:** accuracy on the voltage divider feeds directly into the overvoltage/undervoltage fault logic — a safety decision, not cosmetics.
- **Sealed connectors:** intermittent harness faults from vibration are a classic motorsports failure mode.

---

## Honesty / scope notes

- Selections are **proposed**, not built or tested.
- Reference designators are **indicative** until schematic capture.
- Example MPNs are suitable candidates, **not committed purchases**.
- Current sensing uses a modest non-isolated ACS712 for now; isolated/higher-range sensing is a logged Rev B item.

---

## Open items

- [ ] Confirm MCU against existing `hardware/architecture.md` (assumed ATmega328P).
- [ ] Lock final CAN bitrate (assumed 500 kbit/s) and note it in the message map.
- [ ] Decide current-sense range (20 A prototype vs isolated Rev B).

---

## Next — Day 11 (preview)

Begin **schematic capture / netlist planning**: turn this BOM into a block-by-block schematic, assign real reference designators, and define the power and signal nets. That feeds a future PCB layout and closes the loop from architecture → parts → schematic.
