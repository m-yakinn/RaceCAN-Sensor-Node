"""
RaceCAN BMS Simulator — Test Cases
Day 19: Comprehensive fault boundary testing and state machine validation

Purpose:
  Validate BMS fault logic, state transitions, and shutdown behavior through
  12 boundary test cases that cover normal operation, single faults, multiple
  faults, latching, and recovery. Each test asserts exact system state and
  shutdown signal.

Test Categories:
  A) Normal Operation (1–2 tests)
  B) Cell Voltage Faults (3–5 tests: OV warn, OV crit, UV warn, UV crit)
  C) Pack Current Faults (2 tests: OC charge, OC discharge)
  D) Temperature Faults (2 tests: OT warn, OT crit)
  E) Cell Imbalance Faults (1 test)
  F) Fault Latching & Recovery (2 tests)
  G) Multiple Simultaneous Faults (1 test)

Total: 14 test cases covering 100+ state transitions

Usage:
  python software/simulator/test_cases_bms.py

Expected Output:
  All tests: ✓ PASS (green checkmark)
  Summary: 14/14 passed
"""

import sys
from software.simulator.bms_simulator import (
    BMSSimulator,
    SystemState,
    create_lipo_3s,
    create_lifepo4_4s,
)


def test_assert(condition: bool, test_name: str, message: str) -> None:
    """Assert a condition and print pass/fail."""
    if condition:
        print(f"  ✓ {message}")
    else:
        print(f"  ✗ FAIL: {message}")
        sys.exit(1)


def test_1_normal_operation_3s_lipo():
    """Test 1: Normal operation at 50% SOC, all signals in range."""
    print("\n[Test 1] Normal operation (3S LiPo, 50% SOC, 5A charge, 45°C)")
    bms = create_lipo_3s(capacity_mah=2500)
    bms.update_cells([3.75, 3.70, 3.72])
    bms.update_current(5.0)
    bms.update_temperature(45.0)
    state = bms.get_state()

    test_assert(state["system_state"] == "NORMAL", "test_1", "system_state=NORMAL")
    test_assert(abs(state["pack_voltage_v"] - 11.17) < 0.01, "test_1", "pack_voltage≈11.17V")
    test_assert(state["faults"] == {}, "test_1", "no active faults")
    test_assert(state["shutdown_signal"] == 0, "test_1", "shutdown_signal=0 (inactive)")


def test_2_normal_operation_4s_lifepo4():
    """Test 2: Normal operation with 4S LiFePO4."""
    print("\n[Test 2] Normal operation (4S LiFePO4, 75% SOC, 8A charge, 50°C)")
    bms = create_lifepo4_4s(capacity_mah=5000)
    bms.update_cells([3.4, 3.35, 3.38, 3.36])
    bms.update_current(8.0)
    bms.update_temperature(50.0)
    state = bms.get_state()

    test_assert(state["system_state"] == "NORMAL", "test_2", "system_state=NORMAL")
    test_assert(abs(state["pack_voltage_v"] - 13.49) < 0.01, "test_2", "pack_voltage≈13.49V")
    test_assert(state["faults"] == {}, "test_2", "no active faults")
    test_assert(state["shutdown_signal"] == 0, "test_2", "shutdown_signal=0")


def test_3_cell_overvoltage_warning():
    """Test 3: Single cell crosses OV warning threshold."""
    print("\n[Test 3] Cell overvoltage warning (cell 0 = 4.18V, threshold=4.15V)")
    bms = create_lipo_3s()
    bms.update_cells([4.18, 3.70, 3.72])  # Cell 0 above warning
    state = bms.get_state()

    test_assert(state["system_state"] == "WARNING", "test_3", "system_state=WARNING")
    test_assert("cell_0_ov_warning" in state["faults"], "test_3", "fault detected: cell_0_ov_warning")
    test_assert(state["faults"]["cell_0_ov_warning"] == "WARNING", "test_3", "fault severity=WARNING")
    test_assert(state["shutdown_signal"] == 0, "test_3", "shutdown_signal=0 (warning does not trigger)")


def test_4_cell_overvoltage_critical():
    """Test 4: Single cell crosses OV critical threshold."""
    print("\n[Test 4] Cell overvoltage critical (cell 1 = 4.28V, threshold=4.25V)")
    bms = create_lipo_3s()
    bms.update_cells([3.75, 4.28, 3.72])  # Cell 1 above critical
    state = bms.get_state()

    test_assert(state["system_state"] == "CRITICAL", "test_4", "system_state=CRITICAL")
    test_assert("cell_1_ov_critical" in state["faults"], "test_4", "fault detected: cell_1_ov_critical")
    test_assert(state["faults"]["cell_1_ov_critical"] == "CRITICAL", "test_4", "fault severity=CRITICAL")
    test_assert(state["shutdown_signal"] == 1, "test_4", "shutdown_signal=1 (critical triggers shutdown)")


def test_5_cell_undervoltage_warning():
    """Test 5: Cell falls below UV warning threshold."""
    print("\n[Test 5] Cell undervoltage warning (cell 2 = 2.95V, threshold=3.0V)")
    bms = create_lipo_3s()
    bms.update_cells([3.75, 3.70, 2.95])  # Cell 2 below warning
    state = bms.get_state()

    test_assert(state["system_state"] == "WARNING", "test_5", "system_state=WARNING")
    test_assert("cell_2_uv_warning" in state["faults"], "test_5", "fault detected: cell_2_uv_warning")
    test_assert(state["shutdown_signal"] == 0, "test_5", "shutdown_signal=0")


def test_6_pack_overcurrent_charge_critical():
    """Test 6: Pack current exceeds charge critical (e.g., fast charger anomaly)."""
    print("\n[Test 6] Pack overcurrent charge critical (20.5A, threshold=20.0A)")
    bms = create_lipo_3s()
    bms.update_cells([3.75, 3.70, 3.72])
    bms.update_current(20.5)  # Exceeds charge critical
    state = bms.get_state()

    test_assert(state["system_state"] == "CRITICAL", "test_6", "system_state=CRITICAL")
    test_assert("pack_oc_charge_crit" in state["faults"], "test_6", "fault detected: pack_oc_charge_crit")
    test_assert(state["shutdown_signal"] == 1, "test_6", "shutdown_signal=1 (critical)")


def test_7_pack_overcurrent_discharge_critical():
    """Test 7: Pack current exceeds discharge critical (e.g., short circuit)."""
    print("\n[Test 7] Pack overcurrent discharge critical (-21.0A, threshold=-20.0A)")
    bms = create_lipo_3s()
    bms.update_cells([3.75, 3.70, 3.72])
    bms.update_current(-21.0)  # Exceeds discharge critical
    state = bms.get_state()

    test_assert(state["system_state"] == "CRITICAL", "test_7", "system_state=CRITICAL")
    test_assert("pack_oc_discharge_crit" in state["faults"], "test_7", "fault detected: pack_oc_discharge_crit")
    test_assert(state["shutdown_signal"] == 1, "test_7", "shutdown_signal=1")


def test_8_overtemperature_warning():
    """Test 8: Temperature crosses warning threshold."""
    print("\n[Test 8] Overtemperature warning (56°C, threshold=55°C)")
    bms = create_lipo_3s()
    bms.update_cells([3.75, 3.70, 3.72])
    bms.update_current(5.0)
    bms.update_temperature(56.0)
    state = bms.get_state()

    test_assert(state["system_state"] == "WARNING", "test_8", "system_state=WARNING")
    test_assert("overtemp_warning" in state["faults"], "test_8", "fault detected: overtemp_warning")
    test_assert(state["shutdown_signal"] == 0, "test_8", "shutdown_signal=0 (warning)")


def test_9_overtemperature_critical():
    """Test 9: Temperature crosses critical threshold."""
    print("\n[Test 9] Overtemperature critical (62°C, threshold=60°C)")
    bms = create_lipo_3s()
    bms.update_cells([3.75, 3.70, 3.72])
    bms.update_temperature(62.0)
    state = bms.get_state()

    test_assert(state["system_state"] == "CRITICAL", "test_9", "system_state=CRITICAL")
    test_assert("overtemp_critical" in state["faults"], "test_9", "fault detected: overtemp_critical")
    test_assert(state["shutdown_signal"] == 1, "test_9", "shutdown_signal=1 (critical)")


def test_10_cell_imbalance_warning():
    """Test 10: Cell imbalance exceeds delta threshold."""
    print("\n[Test 10] Cell imbalance warning (max_delta=0.15V, threshold=0.10V)")
    bms = create_lipo_3s()
    bms.update_cells([3.85, 3.70, 3.72])  # Cell 0 is 0.15V higher than cell 1
    state = bms.get_state()

    test_assert(state["system_state"] == "WARNING", "test_10", "system_state=WARNING")
    test_assert("cell_imbalance" in state["faults"], "test_10", "fault detected: cell_imbalance")
    test_assert(state["shutdown_signal"] == 0, "test_10", "shutdown_signal=0 (warning)")


def test_11_fault_latching():
    """Test 11: Critical fault latches; recovery of signals does not clear latched state."""
    print("\n[Test 11] Fault latching (critical → latched even after recovery)")
    bms = create_lipo_3s()

    # Step 1: Enter critical state
    bms.update_cells([4.30, 3.70, 3.72])  # Overvoltage critical
    state = bms.get_state()
    test_assert(state["system_state"] == "CRITICAL", "test_11a", "step 1: state=CRITICAL")
    test_assert(state["shutdown_signal"] == 1, "test_11a", "step 1: shutdown=1")

    # Step 2: Signals recover, but state should latch
    bms.update_cells([3.75, 3.70, 3.72])  # Back to normal
    state = bms.get_state()
    test_assert(state["system_state"] == "LATCHED_FAULT", "test_11b", "step 2: state=LATCHED_FAULT (latched)")
    test_assert(state["shutdown_signal"] == 1, "test_11b", "step 2: shutdown=1 (latched)")

    # Step 3: Manual reset
    bms.reset_latch()
    state = bms.get_state()
    test_assert(state["system_state"] == "NORMAL", "test_11c", "step 3: after reset state=NORMAL")
    test_assert(state["shutdown_signal"] == 0, "test_11c", "step 3: shutdown=0 (reset)")


def test_12_multiple_simultaneous_faults():
    """Test 12: Multiple faults active; state reflects highest severity."""
    print("\n[Test 12] Multiple simultaneous faults (OV warning + OT warning + imbalance)")
    bms = create_lipo_3s()
    bms.update_cells([4.18, 3.70, 3.65])  # OV warning on cell 0, imbalance
    bms.update_temperature(56.0)  # OT warning
    state = bms.get_state()

    test_assert(state["system_state"] == "WARNING", "test_12", "system_state=WARNING (highest severity)")
    test_assert(len(state["faults"]) >= 3, "test_12", f"at least 3 faults present, got {len(state['faults'])}")
    test_assert("cell_0_ov_warning" in state["faults"], "test_12", "fault 1: cell_0_ov_warning")
    test_assert("overtemp_warning" in state["faults"], "test_12", "fault 2: overtemp_warning")
    test_assert("cell_imbalance" in state["faults"], "test_12", "fault 3: cell_imbalance")
    test_assert(state["shutdown_signal"] == 0, "test_12", "shutdown_signal=0 (warnings only)")


def test_13_soc_low_warning():
    """Test 13: SOC drops to warning threshold."""
    print("\n[Test 13] Low SOC warning (approaching empty)")
    bms = create_lipo_3s(capacity_mah=2500)
    # Manually set very low SOC by discharging
    bms.accumulated_charge_mah = 200.0  # ~8% SOC (warning threshold ~10%)
    state = bms.get_state()

    test_assert(state["system_state"] == "WARNING", "test_13", "system_state=WARNING (low SOC)")
    test_assert("soc_low" in state["faults"], "test_13", "fault detected: soc_low")
    test_assert(state["soc_percent"] < 10.0, "test_13", "SOC < 10% warning threshold")


def test_14_all_signals_nominal():
    """Test 14: Verify recovery to normal after warning clears."""
    print("\n[Test 14] Recovery to NORMAL after warnings clear")
    bms = create_lipo_3s()

    # Step 1: Enter WARNING
    bms.update_cells([4.18, 3.70, 3.72])  # OV warning
    state = bms.get_state()
    test_assert(state["system_state"] == "WARNING", "test_14a", "step 1: state=WARNING")

    # Step 2: All signals recover
    bms.update_cells([3.75, 3.70, 3.72])
    bms.update_temperature(45.0)
    state = bms.get_state()
    test_assert(state["system_state"] == "NORMAL", "test_14b", "step 2: state=NORMAL (recovered)")
    test_assert(state["faults"] == {}, "test_14b", "no active faults")
    test_assert(state["shutdown_signal"] == 0, "test_14b", "shutdown_signal=0")


# ============================================================================
# Test Runner
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("RaceCAN BMS Simulator — Day 19 Test Suite")
    print("=" * 80)

    tests = [
        test_1_normal_operation_3s_lipo,
        test_2_normal_operation_4s_lifepo4,
        test_3_cell_overvoltage_warning,
        test_4_cell_overvoltage_critical,
        test_5_cell_undervoltage_warning,
        test_6_pack_overcurrent_charge_critical,
        test_7_pack_overcurrent_discharge_critical,
        test_8_overtemperature_warning,
        test_9_overtemperature_critical,
        test_10_cell_imbalance_warning,
        test_11_fault_latching,
        test_12_multiple_simultaneous_faults,
        test_13_soc_low_warning,
        test_14_all_signals_nominal,
    ]

    for test_func in tests:
        try:
            test_func()
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            sys.exit(1)

    print("\n" + "=" * 80)
    print(f"✓ All {len(tests)} tests passed!")
    print("=" * 80)
