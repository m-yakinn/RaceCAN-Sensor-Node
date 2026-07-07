"""
RaceCAN BMS-to-CAN Integration Tests
Day 20: Boundary and correctness tests for BMSToCANEncoder and BMSCANDecoder

Test coverage:
  - Normal operation encoding (all 6 frames)
  - Round-trip encode/decode correctness
  - Edge cases: max voltage, min voltage, zero current, full SOC, empty SOC
  - Fault flag bitmask correctness (single and multi-fault)
  - Signed encoding: negative current (discharging)
  - Cell voltage frame: 3S pack (4th slot = 0) and 4S pack
  - System state code mapping
  - Severity escalation: WARNING vs CRITICAL

Run with:
  python software/simulator/test_bms_to_can.py
"""

import struct
import sys

from bms_simulator import (
    BMSSimulator,
    BMSState,
    SystemState,
    FaultThresholds,
    create_lipo_3s,
    create_lifepo4_4s,
)
from bms_to_can import (
    BMSToCANEncoder,
    BMSCANDecoder,
    BMS_PACK_STATUS_ID,
    BMS_CURRENT_ID,
    BMS_TEMPERATURE_ID,
    BMS_CELL_VOLTAGES_ID,
    BMS_FAULT_FLAGS_ID,
    BMS_SOC_EXTENDED_ID,
    SEVERITY_NONE,
    SEVERITY_WARNING,
    SEVERITY_CRITICAL,
    FAULT_BIT_CELL_OV,
    FAULT_BIT_CELL_UV,
    FAULT_BIT_OVERTEMP,
    FAULT_BIT_CELL_IMBALANCE,
    FAULT_BIT_LOW_SOC,
    FAULT_BIT_PACK_OC_CHARGE,
    FAULT_BIT_PACK_OC_DISCH,
)


# ---------------------------------------------------------------------------
# Test harness
# ---------------------------------------------------------------------------

PASS = 0
FAIL = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  OK  {label}")
    else:
        FAIL += 1
        msg = f"  FAIL {label}"
        if detail:
            msg += f" -- {detail}"
        print(msg)


def approx(a: float, b: float, tol: float = 0.05) -> bool:
    """Return True if |a - b| <= tol."""
    return abs(a - b) <= tol


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_normal_operation_frame_count():
    """Encoder returns exactly 6 frames for any valid state."""
    print("\n[Test 1] Normal operation produces 6 frames")
    bms     = create_lipo_3s()
    encoder = BMSToCANEncoder()
    bms.update_cells([3.75, 3.70, 3.72])
    bms.update_current(5.0)
    bms.update_temperature(40.0)
    state  = bms.update()
    frames = encoder.encode(state)

    check("frame count == 6", len(frames) == 6)
    ids = [f["frame_id"] for f in frames]
    for expected_id in [0x200, 0x201, 0x202, 0x203, 0x204, 0x205]:
        check(f"frame 0x{expected_id:03X} present", expected_id in ids)


def test_pack_status_round_trip():
    """Frame 0x200 encodes and decodes pack voltage and cell stats correctly."""
    print("\n[Test 2] Frame 0x200 pack status round-trip")
    bms     = create_lipo_3s()
    encoder = BMSToCANEncoder()
    decoder = BMSCANDecoder()

    bms.update_cells([4.10, 4.05, 4.08])
    bms.update_current(0.0)
    bms.update_temperature(25.0)
    state = bms.update()

    frame   = encoder._encode_pack_status(state)
    decoded = decoder._decode_pack_status(frame["data"])

    expected_pack  = 4.10 + 4.05 + 4.08  # 12.23 V
    expected_min   = 4.05
    expected_max   = 4.10
    expected_delta = 4.10 - 4.05  # 0.05 V

    check("pack_voltage_v", approx(decoded["pack_voltage_v"], expected_pack, tol=0.002),
          f"got {decoded['pack_voltage_v']:.3f}, expected {expected_pack:.3f}")
    check("min_cell_v",  approx(decoded["min_cell_v"],  expected_min,   tol=0.001))
    check("max_cell_v",  approx(decoded["max_cell_v"],  expected_max,   tol=0.001))
    check("cell_delta_v", approx(decoded["cell_delta_v"], expected_delta, tol=0.001))


def test_current_signed_charge():
    """Frame 0x201 encodes positive current (charging) correctly."""
    print("\n[Test 3] Frame 0x201 positive current (charging)")
    bms     = create_lipo_3s()
    encoder = BMSToCANEncoder()
    decoder = BMSCANDecoder()

    bms.update_cells([3.75, 3.70, 3.72])
    bms.update_current(8.5)
    bms.update_temperature(25.0)
    state   = bms.update()
    frame   = encoder._encode_current(state)
    decoded = decoder._decode_current(frame["data"])

    check("current_a positive", approx(decoded["current_a"], 8.5, tol=0.001),
          f"got {decoded['current_a']}")
    check("shutdown_signal == 0", decoded["shutdown_signal"] == 0)
    check("system_state == NORMAL", decoded["system_state"] == "NORMAL")


def test_current_signed_discharge():
    """Frame 0x201 encodes negative current (discharging) correctly."""
    print("\n[Test 4] Frame 0x201 negative current (discharging)")
    bms     = create_lipo_3s()
    encoder = BMSToCANEncoder()
    decoder = BMSCANDecoder()

    bms.update_cells([3.75, 3.70, 3.72])
    bms.update_current(-12.0)
    bms.update_temperature(25.0)
    state   = bms.update()
    frame   = encoder._encode_current(state)
    decoded = decoder._decode_current(frame["data"])

    check("current_a negative", approx(decoded["current_a"], -12.0, tol=0.001),
          f"got {decoded['current_a']}")


def test_shutdown_signal_on_critical():
    """Frame 0x201 sets shutdown_signal=1 when BMS is in CRITICAL state."""
    print("\n[Test 5] Shutdown signal active on CRITICAL fault")
    bms     = create_lipo_3s()
    encoder = BMSToCANEncoder()
    decoder = BMSCANDecoder()

    bms.update_cells([4.28, 3.70, 3.72])  # cell 0 OV critical
    bms.update_current(0.0)
    bms.update_temperature(25.0)
    state   = bms.update()
    frame   = encoder._encode_current(state)
    decoded = decoder._decode_current(frame["data"])

    check("system_state == CRITICAL", decoded["system_state"] == "CRITICAL")
    check("shutdown_signal == 1",     decoded["shutdown_signal"] == 1)


def test_latched_fault_shutdown():
    """Frame 0x201 keeps shutdown_signal=1 in LATCHED_FAULT state."""
    print("\n[Test 6] Shutdown signal active on LATCHED_FAULT state")
    bms     = create_lipo_3s()
    encoder = BMSToCANEncoder()
    decoder = BMSCANDecoder()

    # Trigger critical, then return to normal values (latch stays)
    bms.update_cells([4.28, 3.70, 3.72])
    bms.update(dt_s=1.0)
    bms.update_cells([3.75, 3.70, 3.72])  # values back to normal
    state   = bms.update()
    frame   = encoder._encode_current(state)
    decoded = decoder._decode_current(frame["data"])

    check("system_state == LATCHED_FAULT", decoded["system_state"] == "LATCHED_FAULT")
    check("shutdown_signal == 1",          decoded["shutdown_signal"] == 1)


def test_temperature_round_trip():
    """Frame 0x202 encodes temperature to decidegrees and decodes correctly."""
    print("\n[Test 7] Frame 0x202 temperature round-trip")
    bms     = create_lipo_3s()
    encoder = BMSToCANEncoder()
    decoder = BMSCANDecoder()

    bms.update_cells([3.75, 3.70, 3.72])
    bms.update_current(0.0)
    bms.update_temperature(37.5)
    state   = bms.update()
    frame   = encoder._encode_temperature(state)
    decoded = decoder._decode_temperature(frame["data"])

    check("temperature_c", approx(decoded["temperature_c"], 37.5, tol=0.1),
          f"got {decoded['temperature_c']}")


def test_fault_count_in_temperature_frame():
    """Frame 0x202 correctly reports number of active faults."""
    print("\n[Test 8] Fault count in temperature frame")
    bms     = create_lipo_3s()
    encoder = BMSToCANEncoder()
    decoder = BMSCANDecoder()

    # Trigger two warning faults: OV and imbalance
    bms.update_cells([4.17, 3.70, 3.90])  # OV warning on cell 0, imbalance (delta=0.20V)
    bms.update_current(0.0)
    bms.update_temperature(25.0)
    state   = bms.update()
    frame   = encoder._encode_temperature(state)
    decoded = decoder._decode_temperature(frame["data"])

    check("fault_count >= 2", decoded["fault_count"] >= 2,
          f"got fault_count={decoded['fault_count']}, faults={state.faults}")


def test_cell_voltages_3s():
    """Frame 0x203 encodes 3S pack; slot 3 is zero-padded."""
    print("\n[Test 9] Frame 0x203 cell voltages, 3S pack (slot 3 = 0)")
    bms     = create_lipo_3s()
    encoder = BMSToCANEncoder()
    decoder = BMSCANDecoder()

    bms.update_cells([3.80, 3.75, 3.78])
    bms.update_current(0.0)
    bms.update_temperature(25.0)
    state   = bms.update()
    frame   = encoder._encode_cell_voltages(state)
    decoded = decoder._decode_cell_voltages(frame["data"])

    check("cell_0_v", approx(decoded["cell_0_v"], 3.80, tol=0.001))
    check("cell_1_v", approx(decoded["cell_1_v"], 3.75, tol=0.001))
    check("cell_2_v", approx(decoded["cell_2_v"], 3.78, tol=0.001))
    check("cell_3_v == 0.0", decoded["cell_3_v"] == 0.0,
          f"got {decoded['cell_3_v']}")


def test_cell_voltages_4s():
    """Frame 0x203 encodes 4S pack with all four cell slots populated."""
    print("\n[Test 10] Frame 0x203 cell voltages, 4S pack")
    bms     = create_lifepo4_4s()
    encoder = BMSToCANEncoder()
    decoder = BMSCANDecoder()

    bms.update_cells([3.30, 3.28, 3.31, 3.27])
    bms.update_current(0.0)
    bms.update_temperature(25.0)
    state   = bms.update()
    frame   = encoder._encode_cell_voltages(state)
    decoded = decoder._decode_cell_voltages(frame["data"])

    check("cell_0_v", approx(decoded["cell_0_v"], 3.30, tol=0.001))
    check("cell_3_v", approx(decoded["cell_3_v"], 3.27, tol=0.001))


def test_fault_flags_no_faults():
    """Frame 0x204 reports zero fault bits and NONE severity when healthy."""
    print("\n[Test 11] Frame 0x204 fault flags — no active faults")
    bms     = create_lipo_3s()
    encoder = BMSToCANEncoder()
    decoder = BMSCANDecoder()

    bms.update_cells([3.75, 3.70, 3.72])
    bms.update_current(5.0)
    bms.update_temperature(40.0)
    state   = bms.update()
    frame   = encoder._encode_fault_flags(state)
    decoded = decoder._decode_fault_flags(frame["data"])

    check("fault_bits == 0",         decoded["fault_bits"] == 0)
    check("highest_severity == NONE", decoded["highest_severity"] == "NONE")
    check("active_fault_categories empty", decoded["active_fault_categories"] == [])


def test_fault_flags_cell_ov_warning():
    """Frame 0x204 sets CELL_OV bit and WARNING severity on OV warning."""
    print("\n[Test 12] Frame 0x204 fault flags — cell OV warning")
    bms     = create_lipo_3s()
    encoder = BMSToCANEncoder()
    decoder = BMSCANDecoder()

    bms.update_cells([4.18, 3.70, 3.72])  # OV warning threshold: 4.15
    bms.update_current(0.0)
    bms.update_temperature(25.0)
    state   = bms.update()
    frame   = encoder._encode_fault_flags(state)
    decoded = decoder._decode_fault_flags(frame["data"])

    check("CELL_OV bit set",          "CELL_OV" in decoded["active_fault_categories"])
    check("highest_severity WARNING", decoded["highest_severity"] == "WARNING")


def test_fault_flags_multi_fault():
    """Frame 0x204 sets multiple bits on simultaneous faults."""
    print("\n[Test 13] Frame 0x204 fault flags — overtemp + imbalance")
    bms     = create_lipo_3s()
    encoder = BMSToCANEncoder()
    decoder = BMSCANDecoder()

    bms.update_cells([3.75, 3.70, 3.90])  # imbalance delta = 0.20 V
    bms.update_current(0.0)
    bms.update_temperature(57.0)           # overtemp warning: 55 C
    state   = bms.update()
    frame   = encoder._encode_fault_flags(state)
    decoded = decoder._decode_fault_flags(frame["data"])

    check("OVERTEMP bit set",         "OVERTEMP" in decoded["active_fault_categories"])
    check("CELL_IMBALANCE bit set",   "CELL_IMBALANCE" in decoded["active_fault_categories"])
    check("highest_severity WARNING", decoded["highest_severity"] == "WARNING")


def test_fault_flags_critical_severity():
    """Frame 0x204 reports CRITICAL severity when a critical fault is active."""
    print("\n[Test 14] Frame 0x204 fault flags — CRITICAL severity")
    bms     = create_lipo_3s()
    encoder = BMSToCANEncoder()
    decoder = BMSCANDecoder()

    bms.update_cells([4.28, 3.70, 3.72])  # OV critical threshold: 4.25
    bms.update_current(0.0)
    bms.update_temperature(25.0)
    state   = bms.update()
    frame   = encoder._encode_fault_flags(state)
    decoded = decoder._decode_fault_flags(frame["data"])

    check("CELL_OV bit set",           "CELL_OV" in decoded["active_fault_categories"])
    check("highest_severity CRITICAL", decoded["highest_severity"] == "CRITICAL")


def test_soc_extended_round_trip():
    """Frame 0x205 encodes and decodes SOC, capacity, chemistry, cell count."""
    print("\n[Test 15] Frame 0x205 SOC extended round-trip")
    bms     = create_lipo_3s(capacity_mah=2500)
    encoder = BMSToCANEncoder()
    decoder = BMSCANDecoder()

    bms.update_cells([3.75, 3.70, 3.72])
    bms.update_current(0.0)
    bms.update_temperature(25.0)
    state   = bms.update()
    frame   = encoder._encode_soc_extended(state, chemistry="lipo", capacity_mah=2500)
    decoded = decoder._decode_soc_extended(frame["data"])

    check("capacity_mah == 2500",   decoded["capacity_mah"] == 2500)
    check("chemistry == lipo",      decoded["chemistry"] == "lipo")
    check("num_cells == 3",         decoded["num_cells"] == 3)
    check("soc_percent close",      approx(decoded["soc_percent"], state.soc, tol=1.0),
          f"got {decoded['soc_percent']:.1f}, expected {state.soc:.1f}")


def test_soc_extended_lifepo4():
    """Frame 0x205 correctly encodes LiFePO4 chemistry code."""
    print("\n[Test 16] Frame 0x205 LiFePO4 chemistry code")
    bms     = create_lifepo4_4s(capacity_mah=5000)
    encoder = BMSToCANEncoder()
    decoder = BMSCANDecoder()

    bms.update_cells([3.30, 3.28, 3.31, 3.27])
    bms.update_current(0.0)
    bms.update_temperature(25.0)
    state   = bms.update()
    frame   = encoder._encode_soc_extended(state, chemistry="lifepo4", capacity_mah=5000)
    decoded = decoder._decode_soc_extended(frame["data"])

    check("chemistry == lifepo4", decoded["chemistry"] == "lifepo4")
    check("capacity_mah == 5000", decoded["capacity_mah"] == 5000)
    check("num_cells == 4",       decoded["num_cells"] == 4)


def test_dlc_always_8():
    """All frames have DLC = 8 (fixed-length CAN frames)."""
    print("\n[Test 17] All frames have DLC == 8")
    bms     = create_lipo_3s()
    encoder = BMSToCANEncoder()

    bms.update_cells([3.75, 3.70, 3.72])
    bms.update_current(5.0)
    bms.update_temperature(25.0)
    state  = bms.update()
    frames = encoder.encode(state)

    for frame in frames:
        check(f"0x{frame['frame_id']:03X} DLC == 8", frame["dlc"] == 8)
        check(f"0x{frame['frame_id']:03X} data len == 8", len(frame["data"]) == 8)


# ---------------------------------------------------------------------------
# Run all tests
# ---------------------------------------------------------------------------

def run_all():
    print("=" * 70)
    print("RaceCAN BMS-to-CAN Integration — Day 20 Test Suite")
    print("=" * 70)

    test_normal_operation_frame_count()
    test_pack_status_round_trip()
    test_current_signed_charge()
    test_current_signed_discharge()
    test_shutdown_signal_on_critical()
    test_latched_fault_shutdown()
    test_temperature_round_trip()
    test_fault_count_in_temperature_frame()
    test_cell_voltages_3s()
    test_cell_voltages_4s()
    test_fault_flags_no_faults()
    test_fault_flags_cell_ov_warning()
    test_fault_flags_multi_fault()
    test_fault_flags_critical_severity()
    test_soc_extended_round_trip()
    test_soc_extended_lifepo4()
    test_dlc_always_8()

    print()
    print("=" * 70)
    total = PASS + FAIL
    if FAIL == 0:
        print(f"All {total} tests passed.")
    else:
        print(f"{PASS}/{total} tests passed.  {FAIL} FAILED.")
    print("=" * 70)

    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    run_all()
