# Layout Guidelines

**Project:** RaceCAN-Sensor-Node — Formula SAE / Formula E–style low-voltage CAN telemetry node
**Stage:** Day 12 (routing and grounding rules — paper guidelines, no copper routed)
**Status:** Draft ruleset, applies to future KiCad routing

---

## 1. Purpose of This Document

The placement plan says *where parts sit*. This document says *how I intend to connect them* — the grounding strategy, the power routing, and the per-signal routing rules that I would apply once the parts are placed in KiCad. I am writing these as rules with reasoning so that when I route, I am following a documented intent instead of improvising.

> **Honesty note:** No copper has been routed and no design-rule check has been run. These are planned guidelines, not verified results.

---

## 2. Layer Stack

| Layer | Use |
| --- | --- |
| Top | Components and primary signal routing |
| Bottom | Solid ground pour, with short signal routes only where unavoidable |

On a 2-layer board, the bottom copper is my single most valuable resource, so I am spending it on **one continuous ground pour** rather than chopping it up with bottom-side traces. Any bottom-side signal trace I am forced to route punches a slot in that pour and forces return currents to detour around it, so I treat every bottom trace as a cost I have to justify.

---

## 3. Ground Strategy

This is the decision I most want to get right, so I am being explicit about it.

- **One ground plane, not split planes.** The intuitive move is to split "analog ground" and "digital ground" into separate islands. I am deliberately **not** doing that. On a board this size, a split plane usually does more harm than good: high-frequency return currents want to flow directly under their signal trace, and a split forces them to take a long detour, which creates exactly the noise the split was meant to prevent. Instead I keep one solid, uninterrupted ground pour and use **placement** (the buck in one corner, the analog front end in the opposite corner) to keep noisy and quiet currents from sharing copper.
- **Manage return paths by placement.** Because return current follows the signal, my floorplan already separates the loud return currents (buck) from the quiet ones (ADC) physically. The plane stays whole; the separation comes from where the parts are.
- **Quiet analog reference region.** The analog front end gets the part of the plane farthest from the buck. The ADC filter caps reference to ground right at that quiet region, so the voltage the MCU measures is referenced to clean ground.
- **Stitch the plane.** Ground vias near every ground pin and around the board edge/mounting holes keep the plane low-impedance and give vibration-resistant mechanical anchoring.

This "one plane, separate by placement" approach is the modern, defensible answer, and being able to explain *why I did not split the ground* is itself a good interview talking point.

---

## 4. Power Routing

- **Star-style distribution from each rail's source.** `+5V` fans out from the buck output, `+3V3` from the LDO output, rather than daisy-chaining IC to IC, so one IC's current pulses do not modulate the rail another IC sees.
- **Wide power traces.** Power nets (`VIN_RAW`, `VIN_PROT`, `+5V`) are routed wider than signal traces to keep resistance and inductance down. As a 1 oz starting guideline, roughly 0.4–0.5 mm handles the ~1 A class currents here with a modest temperature rise; I will confirm widths against the real currents during routing.
- **Local decoupling at every IC.** Each VCC pin gets its 100 nF cap right at the pin (C4 for U1, C5/C6 for the CAN ICs), with bulk caps (C1/C2/C3) at the rail sources. Decoupling caps do their job by being physically local, so placement and routing of these is non-negotiable.

---

## 5. The Switching Regulator (most important routing rule)

U4 is the noise source, so its routing gets the strictest rules:

- Keep the **hot loop** (input cap → U4 → inductor → output cap → back to input cap) as **small in enclosed area** as possible. Loop area sets how much the switcher radiates.
- Keep the **switch node** copper **small**. It is the fast-swinging node; small copper means a small antenna.
- Tie the regulator's ground return into the main plane with **multiple vias** close to the part.
- Keep the feedback trace short and away from the inductor so switching fields do not corrupt the regulated voltage.
- Route nothing sensitive (no ADC traces, no crystal traces) near or under this loop.

---

## 6. Analog Routing Rules

The analog front end feeds the fault logic, so noise here is a correctness problem, not just a cosmetic one.

- Keep ADC traces **short and direct** from the conditioning cluster to the MCU pin.
- Place each channel's RC filter cap **at the MCU end**, right at the ADC pin.
- Where practical, run a **ground guard** alongside sensitive analog traces, referenced to the quiet plane region.
- Keep all analog routing **away from the buck switch node and away from CANH/CANL**.
- For U6 (ACS712), keep the **high-current `IP+/IP-` path wide and isolated** from the low-level `VIOUT` analog output, so the current being measured does not couple into its own measurement.

---

## 7. CAN Routing Rules

- Route **CANH and CANL as a tight differential pair**: parallel, closely and evenly spaced, length-matched. The bus rejects noise as a pair, so they must travel together.
- Place L2 (common-mode choke), R5 (termination), and D2 (TVS) **right at the J2 connector exit**, in that order, so the bus is filtered, terminated, and clamped where it leaves the board.
- Keep the pair **away from the buck** and from the crystals.
- Keep stubs (the little dead-end branches off the main pair) **short**; long stubs cause reflections on the bus.

---

## 8. Crystal Routing Rules

- Y1 and Y2 traces are **short and symmetric**, with their load caps right at the crystal pins.
- Surround each crystal with a **local ground guard** and stitch it to the plane.
- Keep crystal traces away from the buck and from fast switching signals.

A crystal is both noise-sensitive (it sets timing) and a small emitter (it oscillates), so it gets treated like a tiny analog island.

---

## 9. Clearance, Creepage & Test Access

- The +12 V input section gets **wider clearance** than the logic section. It is still low voltage, but the input is where automotive transients arrive, so I give it margin.
- The ACS712 high-current path gets clearance appropriate to its current and copper.
- I plan **test points / pads** on the key nets — `+5V`, `+3V3`, `GND`, the five ADC channels, `CAN_TX`/`CAN_RX` — so I can probe the board on the bench against the Day 1–9 simulator's expected values. Being able to verify a real reading against a simulated one is the kind of test evidence I want in the portfolio.

---

## 10. Formula E / FSAE Relevance

These rules exist because of how electronics fail on a car, not because they look tidy:

- The **one-plane / separate-by-placement** grounding is what keeps the buck from corrupting the sensor readings the safety logic depends on.
- The **tight buck loop and small switch node** keep the node from radiating into the CAN bus and the rest of the car's electronics.
- The **differential CAN routing with edge filtering/termination/TVS** is what keeps telemetry alive on a noisy, electrically hostile vehicle.
- The **test points** turn "I designed it" into "I can show it reads what the simulator predicted," which is the evidence that matters in a team interview.

---

## 11. Open Items → carried to Day 13

- Translate these rules into KiCad design rules (clearances, trace widths, diff-pair constraints) before routing.
- Confirm power trace widths against the real per-net currents.
- Decide whether any bottom-side signal routing is unavoidable, and if so, where to least damage the ground pour.
