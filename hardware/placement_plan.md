# Placement Plan

**Project:** RaceCAN-Sensor-Node — Formula SAE / Formula E–style low-voltage CAN telemetry node
**Stage:** Day 12 (PCB placement / floorplanning — paper layout intent, nothing captured or routed)
**Status:** Draft floorplan, feeds future KiCad capture and routing

---

## 1. Purpose of This Document

In Day 11 I turned the parts list into a schematic plan: every part got a reference designator, the parts were grouped into six functional blocks, and the power and signal nets were named. That answered *what connects to what*.

Day 12 answers the next question: *where does each part physically sit on the board, and why?* This is the floorplan — the placement decisions that happen before a single trace is routed. On a race car, placement is most of the reliability story. A good schematic that is laid out badly will still pick up switching noise on its sensor readings, radiate on the CAN bus, or crack a solder joint under vibration. So I am treating placement as an engineering deliverable, not an afterthought.

> **Honesty note:** I have not captured this in an EDA tool, run a design-rule check, routed copper, or fabricated anything. This is a planned floorplan with reasoning. Every dimension below is a design intent and a starting target, not a measured result.

---

## 2. Board-Level Decisions

| Decision | Choice | Reasoning |
| --- | --- | --- |
| Layer count | 2-layer (top + bottom), 1.6 mm FR4 | A 4-layer board with dedicated power/ground planes would be electrically better, but a 2-layer board with a solid bottom ground pour is realistic for this scale and forces me to defend my placement instead of hiding sloppy placement behind extra planes. I document the 4-layer upgrade as a Rev B option. |
| Copper weight | 1 oz (35 µm) | Standard, cheap, and adequate for the logic currents. The only high-current path is the ACS712 sense path, which I handle with wide poured copper rather than thicker copper across the whole board. |
| Board shape | Rectangular, connectors on edges | Predictable harness routing on a vehicle; lets me mount the board in an enclosure with the harness entering from defined sides. |
| Target size | ~80 mm × 60 mm (starting estimate) | Comfortable for hand assembly and for the connector footprints; not final until routing confirms it. |
| Mounting | 4 × M3 holes at corners, ground-stitched | Vibration is the enemy on a car. Four corner standoffs and a stiff board reduce flex that cracks solder joints. |

---

## 3. Placement Philosophy

I am placing by **signal flow and by noise**, not by part size. Two ideas drive everything:

1. **Follow the signal.** Power enters at one edge, gets cleaned and regulated, feeds the MCU in the middle, and telemetry leaves on the CAN connector at another edge. Parts that talk to each other sit next to each other so the connecting traces are short.
2. **Separate the aggressor from the victim.** The switching buck regulator (U4) is the loudest electrical thing on the board. The analog front end (the dividers, RC filters, and the ACS712 reading I use for fault decisions) is the most sensitive. These two go in opposite corners, with the digital MCU section as physical and electrical buffer between them.

---

## 4. Board Zones (Floorplan)

I divide the board into five zones. The text diagram below is the intended top-side arrangement (component side), viewed from above.

```
 LEFT EDGE                                              RIGHT EDGE
 +-----------------------------------------------------------------+
 |  ZONE A: POWER IN        |  ZONE B: REGULATION  |               |
 |  J1  Q1  F1  FB1         |  U4 buck  L1         |   ZONE D:     |
 |  D1  C1                  |  U5 LDO   C2 C3      |   CAN         |
 |  (VIN_RAW -> VIN_PROT)   |  (+5V, +3V3)         |   U2 MCP2515  |
 |--------------------------+----------------------|   Y2          |
 |                                                 |   U3 MCP2562  |
 |  ZONE C: DIGITAL / MCU                          |   L2 R5 D2    |
 |  U1 ATmega328P   Y1   J4 ICSP                   |   J2 (CAN)    |
 |  U7 CH340  J5 USB                               |               |
 |-------------------------------------------------+---------------|
 |  ZONE E: ANALOG FRONT END                                       |
 |  R8/R9 divider  NTC ref  RC filters (C10-C14)  clamps (D5-D9)   |
 |  U6 ACS712      J3 (sensor harness)                             |
 +-----------------------------------------------------------------+
 BOTTOM EDGE
```

The key relationships this floorplan enforces:

- **Zone A (power input) is at the far left edge**, so the raw +12 V harness and its protection (Q1 reverse-polarity, F1 fuse, FB1 ferrite, D1 TVS, C1 bulk) stay in one corner and the protected rail flows rightward.
- **Zone B (regulation) sits next to Zone A** so `VIN_PROT` has a short path into the buck. Critically, the buck and its switching components are kept in the upper region, **diagonally as far as possible from Zone E (analog)**.
- **Zone C (digital/MCU) is central**, acting as a buffer. The MCU needs short SPI traces to the CAN controller on its right and short ADC traces down to the analog front end below it, so the center is the natural home.
- **Zone D (CAN) is at the right edge** so CANH/CANL reach the connector with minimal stub, the termination and TVS sit right at the bus exit, and the noisy bus is far from the analog inputs.
- **Zone E (analog front end) runs along the bottom edge**, near its sensor connector J3, and as far from the buck switch node as the board allows.

---

## 5. Per-Block Placement Detail

### 5.1 Zone A — Power Input & Protection

| Refdes | Placement intent |
| --- | --- |
| J1 | Hard against the left board edge; this is where the +12 V harness lands. |
| Q1 | Immediately inside J1 so the reverse-polarity FET is the first thing the raw rail meets. |
| F1, FB1 | In series right after Q1, in physical order `Q1 -> F1 -> FB1`, matching the schematic path. |
| D1 (TVS) | Across `VIN_PROT` to GND, close to where the rail enters the board so it clamps transients before they spread. |
| C1 | Input bulk, next to the regulator input so it also serves the buck. |

A clean reverse-battery and load-dump story is something I want to be able to point to and defend, so the protection parts stay physically grouped and in order rather than scattered.

### 5.2 Zone B — Regulation (the noisy zone)

This is where most of the layout risk lives, because U4 is a switching regulator.

- I keep the **buck hot loop tight**: the input cap, U4, the inductor L1, and the output cap C2 form a small loop with minimal enclosed area. A big switching loop is an antenna.
- The **switch node** (the node between U4 and L1) is kept as small a copper pour as possible. It swings fast and is the main radiator; I do not want it large or routed near anything sensitive.
- The MP1584EN feedback node and its divider stay close to U4, away from the inductor, so switching fields do not couple into the voltage U4 is trying to regulate.
- U5 (the 5 V → 3.3 V LDO) and its caps C19/C20/C3 sit just downstream of the buck output. The LDO is quiet by comparison, so it is not a placement worry.

The whole zone is pushed to the top of the board, diagonally opposite the analog inputs.

### 5.3 Zone C — Digital / MCU

- U1 (ATmega328P) is central. Its decoupling cap C4 goes **directly against the VCC pin**, not somewhere convenient — decoupling only works if it is local.
- Y1 (16 MHz crystal) with its load caps C15/C16 sits **as close to the MCU crystal pins as physically possible**, with short symmetric traces and a local ground guard. A crystal with long traces is both noise-sensitive and a small emitter.
- J4 (ICSP) goes near the board edge for easy programmer access without disturbing the harness.
- U7 (CH340 USB-UART) and J5 (USB) sit at an edge in the digital zone so a bench USB cable can reach them. This is the link that lets my Day 1–9 Python `dashboard.py` and `csv_logger.py` receive live serial data from the physical node.

### 5.4 Zone D — CAN Interface

- U2 (MCP2515) sits between the MCU and U3 so the SPI traces from the MCU are short and the controller-to-transceiver traces are short.
- Y2 (8 MHz crystal) for the controller gets the same close-placement, short-trace treatment as Y1.
- U3 (MCP2562 transceiver) is the last IC before the bus, placed right by J2.
- L2 (common-mode choke), R5 (120 Ω termination), and D2 (CAN TVS) sit **in that order between U3 and the J2 connector**, so the bus is filtered, terminated, and clamped right where it leaves the board. R5 stays jumper-selectable because only the two physical ends of a real CAN bus should be terminated, and I do not know yet whether this node is an end node.

### 5.5 Zone E — Analog Front End

- The five conditioning chains (battery divider R8/R9, NTC reference R10, throttle, brake, current) each keep their `series R -> RC filter cap -> Schottky clamp` group **together as a cluster**, so each channel is a tidy little unit instead of parts spread across the board.
- The RC filter caps C10–C14 are placed at the **MCU end** of each channel, right at the ADC pin they protect, because a filter cap only filters what arrives after it.
- U6 (ACS712-20A) needs special treatment: its high-current path through `IP+`/`IP-` carries real current, so those pads get **wide poured copper**, and the high-current path is kept physically separate from the low-level `VIOUT` analog signal that feeds the ADC.
- J3 (Deutsch sensor connector) is on the bottom edge so the sensor harness lands right at the analog zone.

The 30 k / 10 k battery divider keeps its identity as R8/R9 here, and the 1 % parts matter for placement too: I keep the divider and its filter close and away from the buck so the pack-voltage reading that feeds my overvoltage fault logic is not corrupted by switching noise.

---

## 6. Thermal & Mechanical Notes

- The only meaningful heat source is U4 (buck). Even a buck dissipates some heat; I give it a small copper pour tied to the input/ground for spreading, and I keep electrolytic/film caps from sitting directly against it.
- Mounting holes go at all four corners and are ground-stitched, both for vibration stiffness and to give the ground pour solid mechanical and electrical anchoring.
- Connectors are oriented so harness strain pulls along the board edge, not up off the pads, which is what cracks joints over a season of vibration.

---

## 7. Formula E / FSAE Relevance

Everything in this floorplan maps to a real failure mode on a car:

- **Buck-vs-analog separation** is what keeps a noisy 12 V rail from showing up as jitter on the throttle, brake, current, and pack-voltage readings the fault logic trusts.
- **Edge connectors and strain-relieved orientation** are about surviving vibration and being serviceable in a paddock, not just being neat.
- **CAN filtering/termination/TVS at the connector** is about a telemetry bus that keeps working in an electrically hostile car and does not take down the node if the bus sees a transient.

---

## 8. Open Items → carried to Day 13

- Capture the schematic in KiCad, assign footprints, and generate a netlist for an actual placement pass (this document is the plan that pass would follow).
- Confirm final board dimensions once footprints are placed; the ~80 × 60 mm target may move.
- Decide the 2-layer vs 4-layer question for Rev B based on whether routing the analog zone clean on 2 layers proves awkward.
- Resolve the carried-over `CAN_INT` interrupt-vs-poll decision, since it affects whether PD2 routes to U2.
