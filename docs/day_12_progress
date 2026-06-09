# Day 12 — Progress Log

**Date:** Day 12
**Focus:** PCB placement and layout planning
**Deliverables:** `hardware/placement_plan.md`, `hardware/layout_guidelines.md`, `docs/day12_progress.md`

---

## Summary

Day 11 gave me a schematic plan: every part had a reference designator, the parts were grouped into functional blocks, and the nets were named. On Day 12 I turned that into a physical layout intent — where each part sits on the board and how I intend to ground, power, and route it — without yet capturing or routing anything in an EDA tool.

The core decisions: a 2-layer board with a single solid ground pour, a five-zone floorplan that pushes the switching buck regulator diagonally opposite the analog front end, the MCU central as a buffer, and the CAN interface at its own connector edge. The grounding decision I most want to be able to defend is that I am keeping one continuous ground plane and separating noisy from quiet currents by placement, rather than splitting the ground.

This is still a paper design. Nothing has been captured, routed, design-rule-checked, or fabricated.

---

## What I did today

1. Made the board-level calls: 2-layer 1.6 mm FR4, 1 oz copper, rectangular with edge connectors, ~80 × 60 mm starting target, four ground-stitched corner mounts.
2. Defined a placement philosophy of "follow the signal, separate the aggressor from the victim," with the buck as the aggressor and the analog front end as the victim.
3. Drew a five-zone floorplan: power input (A), regulation (B), digital/MCU (C), CAN (D), analog front end (E).
4. Wrote per-block placement detail keyed to the Day 11 reference designators, including the tight buck hot loop, local decoupling at every VCC pin, close crystal placement, the wide isolated ACS712 current path, and edge-placed connectors.
5. Wrote a layout-guidelines document covering the grounding strategy, power distribution, the switching-regulator routing rules, analog routing, CAN differential routing, crystal routing, clearance/creepage, and planned test points.
6. Tied each major decision back to a real Formula-style failure mode: switching noise on safety-critical readings, CAN survivability, vibration, and serviceability.

---

## Key decisions locked

- [x] 2-layer board with a single continuous ground pour (4-layer noted as a Rev B option).
- [x] Buck regulator and analog front end placed in diagonally opposite corners.
- [x] One ground plane, separation by placement — explicitly not a split-plane design.
- [x] CAN filtering, termination, and TVS placed at the connector exit; termination jumper-selectable.

---

## Open items

- [ ] Capture the schematic in KiCad, assign footprints, and do a real placement pass following this floorplan.
- [ ] Confirm final board size and power trace widths once footprints are placed.
- [ ] Resolve the carried-over `CAN_INT` interrupt-vs-poll decision (affects PD2 routing).
- [ ] Confirm the MP1584EN feedback divider for an exact 5.0 V output.

---

## Next — Day 13 (preview)

Move from layout intent to a first capture: start the KiCad project, bring in the schematic from the Day 11 plan, assign footprints, and translate the Day 12 guidelines into actual KiCad design rules — or, if I want to keep hardware and firmware aligned, update the firmware pin definitions to match the locked schematic pin map. I will confirm which direction at the start of Day 13.
