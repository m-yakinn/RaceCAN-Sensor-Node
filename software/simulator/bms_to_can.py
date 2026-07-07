"""
RaceCAN BMS-to-CAN Integration
Day 20: Translate BMSState into CAN frames 0x200-0x205

Purpose:
  Bridge the BMS simulator (bms_simulator.py) to the RaceCAN CAN protocol.
  Each BMS state update produces up to 6 CAN frames that a receiver can
  decode the same way it decodes the primary telemetry frames (0x100-0x105).

Frame Map (BMS Extension):
  0x200  BMS_PACK_STATUS    pack voltage, min/max cell, delta
  0x201  BMS_CURRENT        current, SOC, shutdown signal, system state
  0x202  BMS_TEMPERATURE    temperature, fault count
  0x203  BMS_CELL_VOLTAGES  individual cell voltages (up to 4 cells)
  0x204  BMS_FAULT_FLAGS    bitmask of active faults and highest severity
  0x205  BMS_SOC_EXTENDED   accumulated charge, capacity, chemistry, cell count

Encoding convention (matches primary protocol):
  - Fixed-point x100 scaling for voltages and current (int16 / uint16)
  - Fixed-point x10 scaling for temperature (int16)
  - Little-endian byte order throughout
  - Signed values: int16 (2's complement)
  - Unsigned values: uint16 or uint8

Usage:
  from software.simulator.bms_simulator import BMSSimulator, create_lipo_3s
  from software.simulator.bms_to_can import BMSToCANEncoder

  bms = create_lipo_3s()
  encoder = BMSToCANEncoder()

  bms.update_cells([3.75, 3.70, 3.72])
  bms.update_current(5.0)
  bms.update_temperature(45.0)
  state = bms.update()

  frames = encoder.encode(state)
  for frame in frames:
      print(frame)
"""

import struct
from typing import List, Dict, Any

from bms_simulator import BMSState, SystemState, FaultThresholds


# ---------------------------------------------------------------------------
# Frame IDs
# ---------------------------------------------------------------------------

BMS_PACK_STATUS_ID    = 0x200
BMS_CURRENT_ID        = 0x201
BMS_TEMPERATURE_ID    = 0x202
BMS_CELL_VOLTAGES_ID  = 0x203
BMS_FAULT_FLAGS_ID    = 0x204
BMS_SOC_EXTENDED_ID   = 0x205

# ---------------------------------------------------------------------------
# Fault bitmask definitions (used in frame 0x204)
# Each bit represents one fault category.
# ---------------------------------------------------------------------------

FAULT_BIT_CELL_OV          = 0  # bit 0: any cell overvoltage
FAULT_BIT_CELL_UV          = 1  # bit 1: any cell undervoltage
FAULT_BIT_PACK_OC_CHARGE   = 2  # bit 2: pack overcurrent charge
FAULT_BIT_PACK_OC_DISCH    = 3  # bit 3: pack overcurrent discharge
FAULT_BIT_OVERTEMP         = 4  # bit 4: overtemperature
FAULT_BIT_CELL_IMBALANCE   = 5  # bit 5: cell imbalance
FAULT_BIT_LOW_SOC          = 6  # bit 6: low state of charge
FAULT_BIT_INTERNAL         = 7  # bit 7: internal error

# Severity codes for frame 0x204 byte 1
SEVERITY_NONE     = 0
SEVERITY_WARNING  = 1
SEVERITY_CRITICAL = 2

# Chemistry codes for frame 0x205 byte 4
CHEMISTRY_LIPO    = 0
CHEMISTRY_LIFEPO4 = 1

# System state codes for frame 0x201 byte 3
STATE_CODE = {
    SystemState.NORMAL:        0,
    SystemState.WARNING:       1,
    SystemState.CRITICAL:      2,
    SystemState.LATCHED_FAULT: 3,
    SystemState.SHUTDOWN:      4,
}


# ---------------------------------------------------------------------------
# Encoder
# ---------------------------------------------------------------------------

class BMSToCANEncoder:
    """
    Encodes a BMSState snapshot into a list of CAN frame dictionaries.

    Each frame dict has:
      frame_id  (int)   : 11-bit CAN standard ID
      dlc       (int)   : data length code (always 8)
      data      (bytes) : 8-byte payload, little-endian
      signals   (dict)  : decoded signal values for human-readable logging
    """

    def encode(self, state: BMSState, chemistry: str = "lipo", capacity_mah: int = 2500) -> List[Dict[str, Any]]:
        """
        Encode a BMSState into all 6 BMS CAN frames.

        Args:
            state       : BMSState returned by BMSSimulator.update()
            chemistry   : "lipo" or "lifepo4" (stored in frame 0x205)
            capacity_mah: pack capacity in mAh (stored in frame 0x205)

        Returns:
            List of 6 frame dicts in ID order (0x200 ... 0x205)
        """
        frames = [
            self._encode_pack_status(state),
            self._encode_current(state),
            self._encode_temperature(state),
            self._encode_cell_voltages(state),
            self._encode_fault_flags(state),
            self._encode_soc_extended(state, chemistry, capacity_mah),
        ]
        return frames

    # -----------------------------------------------------------------------
    # Frame 0x200 — BMS_PACK_STATUS
    # Bytes: [pack_v_lo, pack_v_hi, min_cell_lo, min_cell_hi,
    #         max_cell_lo, max_cell_hi, delta_lo, delta_hi]
    # All values: uint16, millivolts (voltage x 1000), little-endian
    # -----------------------------------------------------------------------

    def _encode_pack_status(self, state: BMSState) -> Dict[str, Any]:
        pack_mv   = int(round(state.pack_voltage * 1000))
        min_mv    = int(round(min(state.cells) * 1000))
        max_mv    = int(round(max(state.cells) * 1000))
        delta_mv  = max_mv - min_mv

        # Clamp to uint16 range [0, 65535]
        pack_mv  = max(0, min(65535, pack_mv))
        min_mv   = max(0, min(65535, min_mv))
        max_mv   = max(0, min(65535, max_mv))
        delta_mv = max(0, min(65535, delta_mv))

        data = struct.pack("<HHHH", pack_mv, min_mv, max_mv, delta_mv)

        return {
            "frame_id": BMS_PACK_STATUS_ID,
            "dlc": 8,
            "data": data,
            "signals": {
                "pack_voltage_mv": pack_mv,
                "min_cell_mv": min_mv,
                "max_cell_mv": max_mv,
                "cell_delta_mv": delta_mv,
            },
        }

    # -----------------------------------------------------------------------
    # Frame 0x201 — BMS_CURRENT
    # Bytes: [current_lo, current_hi, soc, shutdown, state, rsvd, rsvd, rsvd]
    # current: int16, milliamps (current x 1000), signed, little-endian
    # soc    : uint8, 0-100 percent
    # shutdown: uint8, 0=inactive, 1=active
    # state  : uint8, STATE_CODE value
    # -----------------------------------------------------------------------

    def _encode_current(self, state: BMSState) -> Dict[str, Any]:
        current_ma = int(round(state.current * 1000))
        # Clamp to int16 range [-32768, 32767]
        current_ma = max(-32768, min(32767, current_ma))

        soc_byte   = max(0, min(100, int(round(state.soc))))
        shutdown   = state.shutdown_signal
        state_code = STATE_CODE.get(state.system_state, 0)

        data = struct.pack("<hBBBxxx", current_ma, soc_byte, shutdown, state_code)

        return {
            "frame_id": BMS_CURRENT_ID,
            "dlc": 8,
            "data": data,
            "signals": {
                "current_ma": current_ma,
                "soc_percent": soc_byte,
                "shutdown_signal": shutdown,
                "system_state_code": state_code,
                "system_state_name": state.system_state.name,
            },
        }

    # -----------------------------------------------------------------------
    # Frame 0x202 — BMS_TEMPERATURE
    # Bytes: [temp_lo, temp_hi, fault_count, rsvd, rsvd, rsvd, rsvd, rsvd]
    # temp: int16, decidegrees (temperature x 10), signed, little-endian
    # fault_count: uint8, number of active faults
    # -----------------------------------------------------------------------

    def _encode_temperature(self, state: BMSState) -> Dict[str, Any]:
        temp_dC     = int(round(state.temperature * 10))
        temp_dC     = max(-32768, min(32767, temp_dC))
        fault_count = len(state.faults)
        fault_count = max(0, min(255, fault_count))

        data = struct.pack("<hBxxxxx", temp_dC, fault_count)

        return {
            "frame_id": BMS_TEMPERATURE_ID,
            "dlc": 8,
            "data": data,
            "signals": {
                "temperature_dC": temp_dC,
                "temperature_c": state.temperature,
                "fault_count": fault_count,
            },
        }

    # -----------------------------------------------------------------------
    # Frame 0x203 — BMS_CELL_VOLTAGES
    # Bytes: [c0_lo, c0_hi, c1_lo, c1_hi, c2_lo, c2_hi, c3_lo, c3_hi]
    # Each cell: uint16, millivolts, little-endian
    # Unused cell slots filled with 0x0000
    # Supports up to 4 cells (3S or 4S packs)
    # -----------------------------------------------------------------------

    def _encode_cell_voltages(self, state: BMSState) -> Dict[str, Any]:
        cell_mv = []
        for i in range(4):
            if i < len(state.cells):
                mv = int(round(state.cells[i] * 1000))
                mv = max(0, min(65535, mv))
            else:
                mv = 0
            cell_mv.append(mv)

        data = struct.pack("<HHHH", *cell_mv)

        signals = {f"cell_{i}_mv": cell_mv[i] for i in range(4)}

        return {
            "frame_id": BMS_CELL_VOLTAGES_ID,
            "dlc": 8,
            "data": data,
            "signals": signals,
        }

    # -----------------------------------------------------------------------
    # Frame 0x204 — BMS_FAULT_FLAGS
    # Bytes: [fault_bits, severity, rsvd x6]
    # fault_bits: uint8 bitmask (one bit per fault category, see FAULT_BIT_*)
    # severity  : uint8, highest active severity (0=none, 1=warn, 2=crit)
    # -----------------------------------------------------------------------

    def _encode_fault_flags(self, state: BMSState) -> Dict[str, Any]:
        fault_bits = 0
        highest_severity = SEVERITY_NONE

        for fault_id, severity_str in state.faults.items():
            # Map fault key to bitmask position
            if "ov" in fault_id:
                fault_bits |= (1 << FAULT_BIT_CELL_OV)
            if "uv" in fault_id:
                fault_bits |= (1 << FAULT_BIT_CELL_UV)
            if "oc_charge" in fault_id:
                fault_bits |= (1 << FAULT_BIT_PACK_OC_CHARGE)
            if "oc_discharge" in fault_id:
                fault_bits |= (1 << FAULT_BIT_PACK_OC_DISCH)
            if "overtemp" in fault_id:
                fault_bits |= (1 << FAULT_BIT_OVERTEMP)
            if "imbalance" in fault_id:
                fault_bits |= (1 << FAULT_BIT_CELL_IMBALANCE)
            if "soc_low" in fault_id:
                fault_bits |= (1 << FAULT_BIT_LOW_SOC)
            if "internal" in fault_id:
                fault_bits |= (1 << FAULT_BIT_INTERNAL)

            # Track highest severity
            if severity_str == "CRITICAL":
                highest_severity = SEVERITY_CRITICAL
            elif severity_str == "WARNING" and highest_severity < SEVERITY_CRITICAL:
                highest_severity = SEVERITY_WARNING

        data = struct.pack("<BBxxxxxx", fault_bits, highest_severity)

        return {
            "frame_id": BMS_FAULT_FLAGS_ID,
            "dlc": 8,
            "data": data,
            "signals": {
                "fault_bits": fault_bits,
                "fault_bits_bin": format(fault_bits, "08b"),
                "highest_severity": highest_severity,
                "active_faults": list(state.faults.keys()),
            },
        }

    # -----------------------------------------------------------------------
    # Frame 0x205 — BMS_SOC_EXTENDED
    # Bytes: [accum_lo, accum_hi, cap_lo, cap_hi, chemistry, num_cells, rsvd, rsvd]
    # accum    : uint16, accumulated charge in mAh
    # capacity : uint16, total capacity in mAh
    # chemistry: uint8, 0=LiPo, 1=LiFePO4
    # num_cells: uint8, number of cells in series
    # -----------------------------------------------------------------------

    def _encode_soc_extended(self, state: BMSState, chemistry: str, capacity_mah: int) -> Dict[str, Any]:
        # Derive accumulated charge from SOC and capacity
        accum_mah    = int(round((state.soc / 100.0) * capacity_mah))
        accum_mah    = max(0, min(65535, accum_mah))
        capacity_val = max(0, min(65535, int(capacity_mah)))

        chemistry_code = CHEMISTRY_LIFEPO4 if chemistry == "lifepo4" else CHEMISTRY_LIPO
        num_cells      = max(0, min(255, len(state.cells)))

        data = struct.pack("<HHBBxx", accum_mah, capacity_val, chemistry_code, num_cells)

        return {
            "frame_id": BMS_SOC_EXTENDED_ID,
            "dlc": 8,
            "data": data,
            "signals": {
                "accumulated_charge_mah": accum_mah,
                "capacity_mah": capacity_val,
                "chemistry_code": chemistry_code,
                "chemistry_name": chemistry,
                "num_cells": num_cells,
            },
        }


# ---------------------------------------------------------------------------
# Decoder (receiver-side, for validation and dashboard use)
# ---------------------------------------------------------------------------

class BMSCANDecoder:
    """
    Decodes raw CAN frame bytes back into human-readable BMS signal values.
    Used by a receiver (dashboard or test harness) to verify encoder output.
    """

    def decode(self, frame_id: int, data: bytes) -> Dict[str, Any]:
        """Decode a single BMS CAN frame. Returns signal dict or raises ValueError."""
        if frame_id == BMS_PACK_STATUS_ID:
            return self._decode_pack_status(data)
        elif frame_id == BMS_CURRENT_ID:
            return self._decode_current(data)
        elif frame_id == BMS_TEMPERATURE_ID:
            return self._decode_temperature(data)
        elif frame_id == BMS_CELL_VOLTAGES_ID:
            return self._decode_cell_voltages(data)
        elif frame_id == BMS_FAULT_FLAGS_ID:
            return self._decode_fault_flags(data)
        elif frame_id == BMS_SOC_EXTENDED_ID:
            return self._decode_soc_extended(data)
        else:
            raise ValueError(f"Unknown BMS frame ID: 0x{frame_id:03X}")

    def _decode_pack_status(self, data: bytes) -> Dict[str, Any]:
        pack_mv, min_mv, max_mv, delta_mv = struct.unpack("<HHHH", data)
        return {
            "pack_voltage_v": pack_mv / 1000.0,
            "min_cell_v": min_mv / 1000.0,
            "max_cell_v": max_mv / 1000.0,
            "cell_delta_v": delta_mv / 1000.0,
        }

    def _decode_current(self, data: bytes) -> Dict[str, Any]:
        current_ma, soc, shutdown, state_code = struct.unpack("<hBBBxxx", data)
        state_names = {0: "NORMAL", 1: "WARNING", 2: "CRITICAL", 3: "LATCHED_FAULT", 4: "SHUTDOWN"}
        return {
            "current_a": current_ma / 1000.0,
            "soc_percent": soc,
            "shutdown_signal": shutdown,
            "system_state": state_names.get(state_code, "UNKNOWN"),
        }

    def _decode_temperature(self, data: bytes) -> Dict[str, Any]:
        temp_dC, fault_count = struct.unpack("<hBxxxxx", data)
        return {
            "temperature_c": temp_dC / 10.0,
            "fault_count": fault_count,
        }

    def _decode_cell_voltages(self, data: bytes) -> Dict[str, Any]:
        c0, c1, c2, c3 = struct.unpack("<HHHH", data)
        return {
            "cell_0_v": c0 / 1000.0,
            "cell_1_v": c1 / 1000.0,
            "cell_2_v": c2 / 1000.0,
            "cell_3_v": c3 / 1000.0,
        }

    def _decode_fault_flags(self, data: bytes) -> Dict[str, Any]:
        fault_bits, severity = struct.unpack("<BBxxxxxx", data)
        severity_names = {0: "NONE", 1: "WARNING", 2: "CRITICAL"}
        active = []
        bit_names = [
            "CELL_OV", "CELL_UV", "PACK_OC_CHARGE", "PACK_OC_DISCH",
            "OVERTEMP", "CELL_IMBALANCE", "LOW_SOC", "INTERNAL"
        ]
        for i, name in enumerate(bit_names):
            if fault_bits & (1 << i):
                active.append(name)
        return {
            "fault_bits": fault_bits,
            "fault_bits_bin": format(fault_bits, "08b"),
            "active_fault_categories": active,
            "highest_severity": severity_names.get(severity, "UNKNOWN"),
        }

    def _decode_soc_extended(self, data: bytes) -> Dict[str, Any]:
        accum, capacity, chem_code, num_cells = struct.unpack("<HHBBxx", data)
        chem_names = {0: "lipo", 1: "lifepo4"}
        return {
            "accumulated_charge_mah": accum,
            "capacity_mah": capacity,
            "soc_percent": round((accum / capacity * 100.0) if capacity > 0 else 0.0, 1),
            "chemistry": chem_names.get(chem_code, "unknown"),
            "num_cells": num_cells,
        }


# ---------------------------------------------------------------------------
# Convenience helper
# ---------------------------------------------------------------------------

def format_frame(frame: Dict[str, Any]) -> str:
    """Return a human-readable one-line summary of a CAN frame."""
    hex_data = " ".join(f"{b:02X}" for b in frame["data"])
    return f"[0x{frame['frame_id']:03X}] DLC={frame['dlc']} DATA={hex_data}"


# ---------------------------------------------------------------------------
# Example (run standalone for a quick smoke test)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from bms_simulator import create_lipo_3s

    print("=" * 70)
    print("RaceCAN BMS-to-CAN Encoder — Day 20 Smoke Test")
    print("=" * 70)
    print()

    bms     = create_lipo_3s(capacity_mah=2500)
    encoder = BMSToCANEncoder()
    decoder = BMSCANDecoder()

    # Scenario: normal operation
    bms.update_cells([3.75, 3.70, 3.72])
    bms.update_current(5.0)
    bms.update_temperature(45.0)
    state = bms.update()

    print(f"BMS state: {state.system_state.name}  "
          f"pack={state.pack_voltage:.2f}V  "
          f"SOC={state.soc:.1f}%  "
          f"faults={len(state.faults)}")
    print()

    frames = encoder.encode(state, chemistry="lipo", capacity_mah=2500)

    for frame in frames:
        print(format_frame(frame))
        decoded = decoder.decode(frame["frame_id"], frame["data"])
        for k, v in decoded.items():
            print(f"  {k}: {v}")
        print()
