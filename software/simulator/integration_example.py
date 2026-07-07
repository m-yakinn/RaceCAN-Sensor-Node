"""
RaceCAN Integration Example
Day 20: End-to-end demo of BMS simulator feeding the CAN encoder

This script demonstrates the complete RaceCAN software stack:
  1. BMS simulator (bms_simulator.py) generates battery state
  2. BMS-to-CAN encoder (bms_to_can.py) translates state into CAN frames
  3. CAN decoder (bms_to_can.py) receives and decodes frames on the other side

Three scenarios are shown:
  A. Normal operation — all values nominal, no faults
  B. Warning condition — cell imbalance + mild overtemperature
  C. Critical fault and latch — cell overvoltage triggers shutdown

Purpose:
  - Proves the full pipeline: simulate → encode → transmit → decode → display
  - Suitable as a portfolio demonstration or interview code walk-through
  - Shows how a real receiver (dashboard, data logger) would consume BMS data

Run:
  python software/simulator/integration_example.py
"""

from bms_simulator import create_lipo_3s, SystemState
from bms_to_can import BMSToCANEncoder, BMSCANDecoder, format_frame


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def print_separator(title: str) -> None:
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_bms_summary(state) -> None:
    """Print a single-line BMS state summary."""
    print(f"  BMS state   : {state.system_state.name}")
    print(f"  Pack voltage: {state.pack_voltage:.3f} V")
    print(f"  Current     : {state.current:+.2f} A  ({'charging' if state.current >= 0 else 'discharging'})")
    print(f"  Temperature : {state.temperature:.1f} C")
    print(f"  SOC         : {state.soc:.1f} %")
    print(f"  Shutdown    : {'ACTIVE' if state.shutdown_signal else 'inactive'}")
    if state.faults:
        print(f"  Active faults:")
        for fault_id, severity in state.faults.items():
            print(f"    [{severity}] {fault_id}")
    else:
        print("  Active faults: none")


def transmit_and_receive(state, encoder, decoder, chemistry="lipo", capacity_mah=2500) -> None:
    """
    Simulate a CAN bus transmission:
      Encoder side: pack BMSState into CAN frames
      Receiver side: decode each frame and display signals
    """
    frames = encoder.encode(state, chemistry=chemistry, capacity_mah=capacity_mah)

    print()
    print("  -- CAN Bus Transmission --")
    for frame in frames:
        print(f"  TX  {format_frame(frame)}")

    print()
    print("  -- Receiver Decoded Signals --")
    for frame in frames:
        decoded = decoder.decode(frame["frame_id"], frame["data"])
        print(f"  [0x{frame['frame_id']:03X}]")
        for key, value in decoded.items():
            print(f"    {key}: {value}")


# ---------------------------------------------------------------------------
# Scenario A — Normal operation
# ---------------------------------------------------------------------------

def scenario_a(encoder, decoder) -> None:
    print_separator("Scenario A: Normal Operation")
    print()
    print("  Setup: 3S LiPo, balanced cells, 5A charge, 40 C")
    print()

    bms = create_lipo_3s(capacity_mah=2500)
    bms.update_cells([3.80, 3.78, 3.79])
    bms.update_current(5.0)
    bms.update_temperature(40.0)
    state = bms.update()

    print_bms_summary(state)
    transmit_and_receive(state, encoder, decoder)

    # Verify receiver sees expected key signals
    frames  = encoder.encode(state)
    decoded_current = decoder.decode(0x201, next(f for f in frames if f["frame_id"] == 0x201)["data"])
    assert decoded_current["shutdown_signal"] == 0, "Expected no shutdown in normal operation"
    assert decoded_current["system_state"] == "NORMAL", "Expected NORMAL state"
    print()
    print("  Assertion passed: shutdown inactive, system NORMAL")


# ---------------------------------------------------------------------------
# Scenario B — Warning condition
# ---------------------------------------------------------------------------

def scenario_b(encoder, decoder) -> None:
    print_separator("Scenario B: Warning Condition (Imbalance + Temperature)")
    print()
    print("  Setup: cell 2 drifted high (0.22 V delta), temperature at 57 C")
    print()

    bms = create_lipo_3s(capacity_mah=2500)
    bms.update_cells([3.70, 3.72, 3.92])   # 0.22 V imbalance (threshold: 0.10 V)
    bms.update_current(3.0)
    bms.update_temperature(57.0)            # overtemp warning (threshold: 55 C)
    state = bms.update()

    print_bms_summary(state)
    transmit_and_receive(state, encoder, decoder)

    frames  = encoder.encode(state)
    decoded_fault = decoder.decode(0x204, next(f for f in frames if f["frame_id"] == 0x204)["data"])
    assert decoded_fault["highest_severity"] == "WARNING", "Expected WARNING severity"
    assert "CELL_IMBALANCE" in decoded_fault["active_fault_categories"], "Expected imbalance bit"
    assert "OVERTEMP" in decoded_fault["active_fault_categories"], "Expected overtemp bit"
    assert next(f for f in frames if f["frame_id"] == 0x201) is not None

    decoded_current = decoder.decode(0x201, next(f for f in frames if f["frame_id"] == 0x201)["data"])
    assert decoded_current["shutdown_signal"] == 0, "Warning only — shutdown should be inactive"
    print()
    print("  Assertions passed: WARNING severity, imbalance+overtemp bits set, shutdown inactive")


# ---------------------------------------------------------------------------
# Scenario C — Critical fault and latch
# ---------------------------------------------------------------------------

def scenario_c(encoder, decoder) -> None:
    print_separator("Scenario C: Critical Fault and Latch (Cell OV → Shutdown)")
    print()
    print("  Step 1: Cell 0 goes to 4.28 V (OV critical threshold: 4.25 V)")
    print()

    bms = create_lipo_3s(capacity_mah=2500)
    bms.update_cells([4.28, 3.70, 3.72])
    bms.update_current(8.0)
    bms.update_temperature(35.0)
    state = bms.update()

    print_bms_summary(state)
    transmit_and_receive(state, encoder, decoder)

    frames = encoder.encode(state)
    decoded_current = decoder.decode(0x201, next(f for f in frames if f["frame_id"] == 0x201)["data"])
    assert decoded_current["system_state"] == "CRITICAL", "Expected CRITICAL"
    assert decoded_current["shutdown_signal"] == 1, "Expected shutdown active"
    print()
    print("  Assertions passed: CRITICAL state, shutdown active")

    # Now clear the fault condition — latch should remain
    print()
    print("  Step 2: Voltages return to safe range — but latch persists")
    print()
    bms.update_cells([3.75, 3.70, 3.72])
    bms.update_current(2.0)
    state = bms.update()

    print_bms_summary(state)
    transmit_and_receive(state, encoder, decoder)

    frames = encoder.encode(state)
    decoded_current = decoder.decode(0x201, next(f for f in frames if f["frame_id"] == 0x201)["data"])
    assert decoded_current["system_state"] == "LATCHED_FAULT", "Expected LATCHED_FAULT"
    assert decoded_current["shutdown_signal"] == 1, "Expected shutdown still active"
    print()
    print("  Assertions passed: LATCHED_FAULT state, shutdown still active (correct)")

    # Manual reset
    print()
    print("  Step 3: Manual reset of latched fault")
    print()
    bms.reset_latch()
    state = bms.update()

    print_bms_summary(state)

    frames = encoder.encode(state)
    decoded_current = decoder.decode(0x201, next(f for f in frames if f["frame_id"] == 0x201)["data"])
    assert decoded_current["system_state"] == "NORMAL", "Expected NORMAL after reset"
    assert decoded_current["shutdown_signal"] == 0, "Expected shutdown inactive after reset"
    print()
    print("  Assertions passed: NORMAL state restored, shutdown inactive")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("RaceCAN — Day 20 Integration Example")
    print("BMS Simulator -> CAN Encoder -> CAN Bus -> CAN Decoder")
    print("=" * 70)

    encoder = BMSToCANEncoder()
    decoder = BMSCANDecoder()

    scenario_a(encoder, decoder)
    scenario_b(encoder, decoder)
    scenario_c(encoder, decoder)

    print()
    print("=" * 70)
    print("All three scenarios completed. Integration verified.")
    print("=" * 70)


if __name__ == "__main__":
    main()
