# Day 11 — Progress Log

**Date:** Day 11
**Focus:** Schematic capture / netlist planning
**Deliverables:** `hardware/schematic_plan.md`, `hardware/netlist.md`, `docs/day11_progress.md`

---

## Summary

Day 10 gave me a justified parts list. On Day 11 I turned that list into a block-by-block schematic plan: I assigned a reference designator to every part, organized the parts into six functional blocks (power input/protection, regulation, MCU, CAN interface, analog conditioning, indicators/debug), and defined the named power and signal nets that tie them together.

This is the step that makes the design real on paper — it closes the chain of architecture → parts → schematic and sets up a PCB layout. Nothing was captured in an EDA tool, simulated, or built. This is a planned schematic with reasoning.

---

## What I did today

1. Locked the three open items from Day 10: MCU = ATmega328P (the architecture doc names no other MCU and the firmware is 10-bit), CAN bitrate = 500 kbit/s, current sense = ACS712-20A for the Tier B board.
2. Defined a board-wide reference designator convention and assigned a designator to every selected part.
3. Mapped the ATmega328P pins to named nets, keeping the Arduino aliases so the schematic reads the same way my firmware does.
4. Wrote the per-channel analog conditioning chain (series R → RC filter → BAT54S clamp) as concrete components on five ADC channels, with the iconic 30 k / 10 k battery divider now formally R8 / R9.
5. Planned the CAN section as MCP2515 + MCP2562 with a common-mode choke, jumper-selectable 120 Ω termination, and a bus TVS at the connector.
6. Wrote a planned netlist listing every power and signal net with its primary nodes, plus a connector pinout summary.

---

## Open items

- [ ] Capture the plan in KiCad and run an electrical-rules check.
- [ ] Confirm the MP1584EN feedback divider for an exact 5.0 V output.
- [ ] Decide whether `CAN_INT` is interrupt-driven or polled.

---

## Next — Day 12 (preview)

PCB placement and layout planning: component grouping, ground-plane strategy, keeping the noisy switching regulator away from the analog front end, and placing connectors at the board edge. This turns the schematic plan into a physical layout intent.
