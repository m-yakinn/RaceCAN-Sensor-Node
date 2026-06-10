# Input Protection Deep-Dive

**Project:** RaceCAN-Sensor-Node — Formula SAE / Formula E–style low-voltage CAN telemetry node
**Stage:** Day 13 (input protection analysis — paper analysis, nothing built or bench-tested)
**Status:** Design rationale for every protection element already in the schematic plan

---

## 1. Purpose of This Document

Days 11 and 12 placed protection parts on the schematic and the floorplan: series resistors, RC filters, Schottky clamps, a TVS at the power input, a PTC fuse, a reverse-polarity FET, and a TVS plus choke on the CAN bus. Day 13 is where I defend each of those parts. For every element I answer three questions: what fault is it there to absorb, what are the numbers that say it survives that fault, and what happens if I removed it.

This matters because on a car, the inputs are where the outside world attacks the board. A sensor harness on a vehicle gets pinched, chafed, miswired, disconnected while powered, and zapped by a mechanic's ESD. A node whose ADC pins die the first time a throttle wire rubs against the +12 V feed is not a telemetry node, it is a fuse.

> **Honesty note:** I have not built or bench-tested any of this. The calculations below are design analysis on the planned circuit, using datasheet limits. Where I cite a component rating, it comes from the manufacturer datasheet; where I compute a current or power, it is a worst-case hand calculation, not a measurement.

---

## 2. Threat Model — What Can Actually Arrive at Each Input

Before sizing parts, I list the faults I am designing against. This is the input-protection equivalent of a requirements list.

| # | Fault | Where it arrives | Why it happens on a car |
| --- | --- | --- | --- |
| T1 | Reverse battery | J1 power input | Battery connected backwards in the paddock |
| T2 | Overvoltage transient / load dump class surge | J1 power input | Inductive loads switching, alternator/charger behavior, jump start |
| T3 | Sensor wire shorted to +12 V | Any J3 analog pin | Chafed harness insulation against the 12 V feed |
| T4 | Sensor wire shorted to GND | Any J3 analog pin | Chafed insulation against chassis ground |
| T5 | Sensor wire open / disconnected | Any J3 analog pin | Vibration-loosened pin, broken crimp |
| T6 | ESD at any connector | J1, J2, J3, J5 | Human handling during service |
| T7 | Switching and ignition noise coupled into sensor lines | J3 analog pins | Long harness runs acting as antennas |
| T8 | CAN bus transient / miswire | J2 | Bus wiring faults, transients coupled onto the pair |
| T9 | Overcurrent into the board | J1 | Downstream short on the board itself |

Every protection component below exists to absorb at least one row of this table, and I name which.

---

## 3. Power Input Chain (T1, T2, T6, T9)

The path is `J1 -> Q1 -> F1 -> FB1 -> VIN_PROT`, with D1 clamping `VIN_PROT` to GND and C1 as bulk.

### 3.1 Q1 (DMP3098L P-FET) — reverse battery (T1)

The P-FET sits high-side with its gate pulled toward ground through R2 (100 k) via R1 (100 ohm). With correct polarity, the gate is well below the source, the FET enhances fully, and the drop across it is just R_DS(on) times the load current — millivolts, with essentially no wasted power. With the battery reversed, the gate-source voltage cannot enhance the FET and the body diode is also reverse-biased, so the board sees no current at all.

Why a FET and not a series diode: a simple series diode would also block reverse current, but it burns a forward-voltage drop continuously (roughly 0.3 to 0.7 V at the node's supply current) and lowers the voltage the buck sees. The FET gives the same protection at near-zero cost in drop. This is the trade I want to be able to explain in an interview.

What I check against the datasheet: V_GS maximum. With a 12 V rail, the gate network must keep V_GS within the FET's rating; R1/R2 form the divider-and-limit structure for that, and confirming the exact V_GS at maximum expected input voltage is an open item for the KiCad capture pass.

### 3.2 F1 (PTC resettable fuse) — overcurrent (T9)

If something downstream on the board shorts, F1 heats and goes high-resistance, limiting the fault current instead of letting the harness wiring become the fuse. I chose a resettable PTC over a one-shot fuse because this is a development board that will see mistakes; a PTC recovers after the fault is removed instead of needing a part swap in the paddock. The trip current must sit above the node's worst-case operating current with margin, which I will finalize against the measured board current — for now the node's budget is well under 500 mA, dominated by the MCU, CAN pair, and the LEDs.

### 3.3 D1 (SMBJ24A TVS) — input transients (T2, T6)

The SMBJ24A stands off 24 V continuously, which means it is invisible at the normal 12 to 14.5 V system voltage and even during a 24 V jump-start scenario. When a fast transient drives the rail above its breakdown (around 26.7 V), it avalanches and clamps, absorbing the surge energy and holding the rail to its clamping voltage (worst case around 38.9 V at full rated pulse current for this part).

The reasoning chain that matters: the buck (U4, MP1584EN) has a maximum input rating of 28 V. The TVS does not keep the rail at 12 V during a surge — no
