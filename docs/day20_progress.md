# Day 20 — BMS-to-CAN Integration

**Date:** Day 20
**Focus:** Bridge the BMS simulator to the RaceCAN CAN protocol by encoding BMSState into six CAN frames (0x200–0x205) and decoding them on the receiver side
**Deliverables:** `software/simulator/bms_to_can.py`, `software/simulator/test_bms_to_can.py`, `software/simulator/integration_example.py`

---

## Summary

Day 19 built a complete BMS simulator with a five-state fault machine, Coulomb-counted SOC, and active-high shutdown signal. The simulator produced Python dicts. Day 20 closes the last gap: encoding that output as real CAN frames that a receiver can decode with the same toolchain used for the primary telemetry protocol (0x100–0x105).

The result is a six-frame BMS extension protocol (0x200–0x205), a round-trip encoder/decoder pair, 17 integration tests, and an end-to-end scenario script. The full RaceCAN software stack is now complete.

---

## What Was Built

### 1. BMS CAN Frame Map

Six frames extend the primary protocol. All follow the same encoding conventions established in Days 15–18: fixed-point scaling, little-endian byte order, unsigned values as uint16/uint8, signed values as int16.

| Frame ID | Name               | Key Signals                                              |
|----------|--------------------|----------------------------------------------------------|
| 0x200    | BMS_PACK_STATUS    | pack_voltage_mv, min_cell_mv, max_cell_mv, cell_delta_mv |
| 0x201    | BMS_CURRENT        | current_ma (int16), soc_percent, shutdown_signal, system_state |
| 0x202    | BMS_TEMPERATURE    | temperature_dC (int16, x10 scaling), fault_count        |
| 0x203    | BMS_CELL_VOLTAGES  | cell_0_mv … cell_3_mv (uint16 each, unused slots = 0)   |
| 0x204    | BMS_FAULT_FLAGS    | fault_bits (uint8 bitmask), highest_severity (uint8)    |
| 0x205    | BMS_SOC_EXTENDED   | accumulated_charge_mah, capacity_mah, chemistry, num_cells |

All frames are fixed DLC = 8.

#### Encoding decisions

**Voltages use millivolt resolution (x1000 scaling)** rather than the x100 scaling used in primary frames. Cell voltages live in the range 2.0–4.2 V. At x100 scaling a cell at 4.20 V would encode as 420 — only 10 counts of margin before a 3S pack sum (12.60 V → 1260) fits in uint16. At x1000 scaling cell_mv values are 2000–4200 and pack_mv for a 3S pack peaks at 12600, all safely within uint16 (0–65535).

**Current uses milliamp resolution (x1000 scaling), int16.** The ACS712-20A range is ±20 A, so ±20000 mA fits well within int16 (±32767 mA). Positive = charging, negative = discharging — matching the BMS simulator convention.

**Temperature uses decidegree resolution (x10 scaling), int16.** A range of −3276.8 °C to +3276.7 °C covers all realistic operating and fault temperatures.

**Frame 0x204 fault_bits is a bitmask**, one bit per fault category:

| Bit | Category         |
|-----|-----------------|
| 0   | CELL_OV         |
| 1   | CELL_UV         |
| 2   | PACK_OC_CHARGE  |
| 3   | PACK_OC_DISCH   |
| 4   | OVERTEMP        |
| 5   | CELL_IMBALANCE  |
| 6   | LOW_SOC         |
| 7   | INTERNAL        |

A bitmask is more compact than individual bytes per fault and matches the pattern used in automotive ECU diagnostics (DTC flags). A receiver can check a single byte to determine which fault categories are active without parsing multiple fields.

### 2. BMSToCANEncoder (`software/simulator/bms_to_can.py`)

The encoder takes a `BMSState` (returned by `BMSSimulator.update()`) and returns a list of six frame dicts:

```python
from bms_simulator import create_lipo_3s
from bms_to_can import BMSToCANEncoder

bms     = create_lipo_3s(capacity_mah=2500)
encoder = BMSToCANEncoder()

bms.update_cells([3.75, 3.70, 3.72])
bms.update_current(5.0)
bms.update_temperature(40.0)
state = bms.update()

frames = encoder.encode(state, chemistry="lipo", capacity_mah=2500)
# Returns list of 6 dicts: {frame_id, dlc, data (bytes), signals (dict)}
```

Each frame dict contains the raw `data` bytes for CAN transmission and a `signals` dict for human-readable logging.

### 3. BMSCANDecoder (`software/simulator/bms_to_can.py`)

The decoder reconstructs signal values from raw bytes. A receiver only needs the frame ID and 8-byte payload:

```python
from bms_to_can import BMSCANDecoder

decoder = BMSCANDecoder()
decoded = decoder.decode(0x201, raw_bytes)
# Returns: {'current_a': 5.0, 'soc_percent': 50, 'shutdown_signal': 0, 'system_state': 'NORMAL'}
```

The decoder is symmetric with the encoder: decode(encode(state)) returns values that match the original state within quantization error.

### 4. Test Suite (`software/simulator/test_bms_to_can.py`)

17 tests covering:

| Test | Scenario |
|------|----------|
| 1  | Encoder produces exactly 6 frames, all IDs present |
| 2  | Frame 0x200 pack voltage, min/max cell, delta round-trip |
| 3  | Frame 0x201 positive current (charging) |
| 4  | Frame 0x201 negative current (discharging) |
| 5  | Frame 0x201 shutdown_signal=1 on CRITICAL state |
| 6  | Frame 0x201 shutdown_signal=1 on LATCHED_FAULT state |
| 7  | Frame 0x202 temperature round-trip (decidegree scaling) |
| 8  | Frame 0x202 fault_count >= 2 on multi-fault scenario |
| 9  | Frame 0x203 3S pack: cell 3 slot is zero-padded |
| 10 | Frame 0x203 4S pack: all cell slots populated |
| 11 | Frame 0x204 no active faults: bits=0, severity=NONE |
| 12 | Frame 0x204 OV warning: CELL_OV bit set, severity=WARNING |
| 13 | Frame 0x204 imbalance + overtemp: two bits set simultaneously |
| 14 | Frame 0x204 OV critical: severity=CRITICAL |
| 15 | Frame 0x205 SOC, capacity, chemistry, cell count round-trip |
| 16 | Frame 0x205 LiFePO4 chemistry code |
| 17 | All frames have DLC=8 and data length=8 |

All 17 tests pass.

### 5. Integration Example (`software/simulator/integration_example.py`)

Three end-to-end scenarios demonstrating the full pipeline:

**Scenario A — Normal operation.** 3S LiPo, balanced cells, 5A charge, 40°C. All six frames encode and decode correctly. Shutdown inactive, system NORMAL.

**Scenario B — Warning condition.** Cell 2 drifted to 3.92 V (0.22 V imbalance, threshold 0.10 V) and temperature at 57°C (threshold 55°C). Frame 0x204 reports CELL_IMBALANCE and OVERTEMP bits set, severity=WARNING. Shutdown remains inactive — warning conditions do not trigger shutdown.

**Scenario C — Critical fault and latch.** Cell 0 at 4.28 V (OV critical threshold 4.25 V). Step 1: CRITICAL state, shutdown=1. Step 2: voltages return to safe range — system enters LATCHED_FAULT, shutdown=1 remains (latch prevents auto-recovery). Step 3: manual reset — NORMAL state restored, shutdown=0.

---

## Locked Decisions

1. **Millivolt resolution for all voltage signals in BMS frames**
   Using x1000 scaling instead of x100 avoids overflow on 4S pack voltages and preserves 1 mV resolution — sufficient for cell monitoring without exceeding uint16.

2. **Current encoded as int16 milliamps (x1000 scaling)**
   Matches the ±20 A range of the ACS712-20A. Signed encoding is necessary because the BMS monitors both charge and discharge direction.

3. **Temperature encoded as int16 decidegrees (x10 scaling)**
   Single decimal place resolution is sufficient for temperature monitoring. Signed to handle sub-zero ambient conditions.

4. **Fault bitmask in frame 0x204 rather than per-fault bytes**
   A bitmask is compact, readable in hex, and matches automotive DTC convention. A receiver can evaluate all fault categories with a single byte comparison.

5. **Cell voltage frame supports up to 4 cells; unused slots are zero-padded**
   Keeps the frame format identical for 3S and 4S packs. Receiver knows num_cells from frame 0x205 and ignores zero-padded slots accordingly.

6. **Decoder is symmetric with encoder**
   Every signal that is encoded can be fully recovered by the decoder, within the quantization error of the fixed-point scaling. This is verified by the round-trip tests.

---

## Open Items

1. **Dashboard integration (Phase 2)**
   The BMS frames are ready to feed a dashboard display. Frame 0x201 system_state and shutdown_signal are natural candidates for a fault banner or status indicator.

2. **CAN frame scheduling interval**
   The primary protocol (0x100–0x105) transmits at 100 ms intervals. BMS frames could transmit at 100 ms or at a lower priority 500 ms rate. This decision is deferred to firmware implementation.

3. **Fault history logging**
   The BMS simulator maintains `fault_history` internally but it is not currently encoded into a CAN frame. A seventh frame (0x206 BMS_FAULT_LOG) could carry a ring-buffer entry per transmission, allowing the dashboard to reconstruct fault history over the bus.

4. **MP1584EN feedback divider, SPI pin conflict, interrupt vs poll**
   Carried forward from earlier sessions. These remain open hardware/firmware decisions.

---

## Why This Matters for the Portfolio

**Interview talking point:**

> "After building the BMS fault state machine on Day 19, I needed to get that data onto a CAN bus. On Day 20 I designed a six-frame extension protocol using the same encoding conventions as the primary telemetry — fixed-point scaling, little-endian, fixed DLC 8. I wrote both the encoder and the decoder so I could verify the full round-trip in tests without needing physical hardware. The key design decision was using millivolt resolution for cell voltages instead of the centivolt resolution I used for pack voltage in the primary protocol — because cell voltages in a LiPo pack live between 2.0 V and 4.2 V and I needed 1 mV resolution to detect imbalance accurately."

**Technical evidence:**
- Six CAN frames with defined IDs, scaling, and byte layout
- Symmetric encode/decode pair with quantization-error-bounded round-trips
- 17 integration tests, all passing
- Three end-to-end scenarios including fault latch and recovery
- Consistent with primary protocol encoding conventions (Days 15–18)

---

## Testing

```bash
# Unit and integration tests
python software/simulator/test_bms_to_can.py

# End-to-end scenario demonstration
python software/simulator/integration_example.py
```

---

## Day 21 Preview (Phase 5 — Closing the Loop)

Phase 5 shifts from software construction to consolidation and knowledge validation:

1. **Loose ends cleanup** — rename `docs/day_12_progress.md` (underscore inconsistency), update `future_roadmap.md` status fields to reflect completed phases, audit and cross-link all progress logs.

2. **Knowledge assessment** — interactive Q&A sessions covering protocol design, firmware architecture, fault logic, and state machine design. Each session poses questions and validates answers before moving on.

3. **Circuitry testing** — questions on the hardware design: MP1584EN feedback divider calculation, TVS diode selection, ACS712 current sense circuit, MCP2515/MCP2562 SPI and CAN interface, reverse polarity protection topology, and decoupling capacitor placement strategy.

The goal is to ensure the project can be explained from first principles in an interview, not just described at a high level.
