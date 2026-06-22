"""
RaceCAN BMS Simulator
Day 19: Battery Management System with fault state machine and safety logic

Purpose:
  Demonstrates low-voltage battery monitoring (3S/4S conceptual), fault detection,
  state machine logic, and shutdown signal generation. This is the "where safety lives"
  in Formula E — BMS decisions protect the battery and the vehicle.

Scope:
  - Cell voltage monitoring (3S or 4S LiPo/LiFePO4 chemistry model)
  - Pack voltage, current, temperature tracking
  - SOC (State of Charge) estimation via Coulomb counting
  - Fault state machine: NORMAL → WARNING → CRITICAL → LATCHED_FAULT → SHUTDOWN
  - Configurable thresholds (cell OV, UV, pack OC, OT, imbalance)
  - Active-high shutdown signal generation
  - CAN telemetry ready (can integrate with RaceCAN 0x100–0x105 protocol)

Chemistry:
  - Cell nominal voltage: 3.7 V (LiPo) or 3.2 V (LiFePO4)
  - Cell full voltage: 4.2 V (LiPo) or 3.6 V (LiFePO4)
  - Cell empty voltage: 2.7 V (LiPo) or 2.0 V (LiFePO4)
  - Typical capacity: 2000–5000 mAh per cell (configurable)

Usage:
  from software.simulator.bms_simulator import BMSSimulator
  
  bms = BMSSimulator(chemistry='lipo', num_cells=3, capacity_mah=2500)
  bms.update_cells([3.75, 3.70, 3.72])  # Cell voltages in V
  bms.update_current(5.0)                # Charging current in A
  bms.update_temperature(45.0)           # Cell temperature in C
  
  state = bms.get_state()
  print(f"State: {state['system_state']}, Shutdown: {state['shutdown_signal']}")
"""

import time
from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass, field


class SystemState(Enum):
    """BMS system state machine."""
    NORMAL = 0
    WARNING = 1
    CRITICAL = 2
    LATCHED_FAULT = 3
    SHUTDOWN = 4


class FaultType(Enum):
    """Individual fault types."""
    CELL_OVERVOLTAGE = "cell_overvoltage"
    CELL_UNDERVOLTAGE = "cell_undervoltage"
    PACK_OVERCURRENT_CHARGE = "pack_overcurrent_charge"
    PACK_OVERCURRENT_DISCHARGE = "pack_overcurrent_discharge"
    OVERTEMPERATURE = "overtemperature"
    CELL_IMBALANCE = "cell_imbalance"
    LOW_SOC = "low_soc"
    INTERNAL_ERROR = "internal_error"


@dataclass
class FaultThresholds:
    """Configurable fault thresholds for different chemistries."""
    # Cell voltage thresholds (V)
    cell_ov_warning: float = 4.15
    cell_ov_critical: float = 4.25
    cell_uv_warning: float = 3.0
    cell_uv_critical: float = 2.8

    # Pack current thresholds (A)
    pack_oc_charge_warning: float = 18.0
    pack_oc_charge_critical: float = 20.0
    pack_oc_discharge_warning: float = 18.0
    pack_oc_discharge_critical: float = 20.0

    # Temperature thresholds (°C)
    temp_warning: float = 55.0
    temp_critical: float = 60.0

    # Cell imbalance (max V difference between cells)
    imbalance_warning_delta: float = 0.1

    # SOC thresholds (%)
    soc_low_warning: float = 10.0


@dataclass
class BMSState:
    """Current BMS state snapshot."""
    system_state: SystemState
    cells: List[float]  # Individual cell voltages (V)
    pack_voltage: float  # Sum of cell voltages (V)
    current: float  # Current (A, positive=charge, negative=discharge)
    temperature: float  # Pack temperature (°C)
    soc: float  # State of charge (%)
    faults: Dict[str, str]  # Active faults {fault_id: severity}
    shutdown_signal: int  # 0=inactive, 1=active (shutdown BMS)
    timestamp_ms: float = field(default_factory=lambda: time.time() * 1000)


class BMSSimulator:
    """Low-voltage BMS simulator with fault logic and state machine."""

    def __init__(
        self,
        chemistry: str = "lipo",
        num_cells: int = 3,
        capacity_mah: int = 2500,
        thresholds: Optional[FaultThresholds] = None,
    ):
        """
        Initialize BMS simulator.

        Args:
            chemistry: "lipo" or "lifepo4"
            num_cells: Number of cells in series (typically 3S or 4S)
            capacity_mah: Total pack capacity in mAh
            thresholds: Custom FaultThresholds; uses defaults if None
        """
        self.chemistry = chemistry
        self.num_cells = num_cells
        self.capacity_mah = capacity_mah
        self.thresholds = thresholds or FaultThresholds()

        # Initialize chemistry-specific defaults
        if chemistry == "lipo":
            self.cell_nominal = 3.7
            self.cell_full = 4.2
            self.cell_empty = 2.7
        elif chemistry == "lifepo4":
            self.cell_nominal = 3.2
            self.cell_full = 3.6
            self.cell_empty = 2.0
        else:
            raise ValueError(f"Unknown chemistry: {chemistry}")

        # State variables
        self.cells = [self.cell_nominal] * num_cells
        self.current = 0.0
        self.temperature = 25.0
        self.soc = 50.0  # 50% initial state of charge
        self.accumulated_charge_mah = (self.capacity_mah * self.soc) / 100.0

        # State machine
        self.system_state = SystemState.NORMAL
        self.active_faults: Dict[str, str] = {}  # {fault_id: severity}
        self.fault_history: List[str] = []

        # Shutdown latch (once critical, stays critical until reset)
        self.latched_fault = False

    def update_cells(self, cell_voltages: List[float]) -> None:
        """Update individual cell voltages (V)."""
        if len(cell_voltages) != self.num_cells:
            raise ValueError(
                f"Expected {self.num_cells} cells, got {len(cell_voltages)}"
            )
        self.cells = cell_voltages

    def update_current(self, current_a: float) -> None:
        """Update pack current (A, positive=charge, negative=discharge)."""
        self.current = current_a

    def update_temperature(self, temp_c: float) -> None:
        """Update pack temperature (°C)."""
        self.temperature = temp_c

    def _update_soc(self, dt_s: float = 1.0) -> None:
        """Update SOC via Coulomb counting."""
        # Simple Coulomb counter: coulombs_in = amps * seconds / 3600
        dq_mah = (self.current * dt_s) / 3.6  # mAh accumulated
        self.accumulated_charge_mah += dq_mah

        # Clamp to valid range [0, capacity_mah]
        self.accumulated_charge_mah = max(0, min(self.capacity_mah, self.accumulated_charge_mah))

        # Convert to SOC (%)
        self.soc = (self.accumulated_charge_mah / self.capacity_mah) * 100.0

    def _check_faults(self) -> Dict[str, str]:
        """
        Evaluate all fault conditions and return active faults.

        Returns:
            dict: {fault_id: severity} where severity is "WARNING" or "CRITICAL"
        """
        faults = {}

        # ===== Cell Voltage Faults =====
        for i, cell_v in enumerate(self.cells):
            if cell_v >= self.thresholds.cell_ov_critical:
                faults[f"cell_{i}_ov_critical"] = "CRITICAL"
            elif cell_v >= self.thresholds.cell_ov_warning:
                faults[f"cell_{i}_ov_warning"] = "WARNING"

            if cell_v <= self.thresholds.cell_uv_critical:
                faults[f"cell_{i}_uv_critical"] = "CRITICAL"
            elif cell_v <= self.thresholds.cell_uv_warning:
                faults[f"cell_{i}_uv_warning"] = "WARNING"

        # ===== Cell Imbalance =====
        if len(self.cells) > 1:
            cell_max = max(self.cells)
            cell_min = min(self.cells)
            delta = cell_max - cell_min
            if delta > self.thresholds.imbalance_warning_delta:
                faults["cell_imbalance"] = "WARNING"

        # ===== Pack Current Faults =====
        if self.current >= self.thresholds.pack_oc_charge_critical:
            faults["pack_oc_charge_crit"] = "CRITICAL"
        elif self.current >= self.thresholds.pack_oc_charge_warning:
            faults["pack_oc_charge_warn"] = "WARNING"

        if self.current <= -self.thresholds.pack_oc_discharge_critical:
            faults["pack_oc_discharge_crit"] = "CRITICAL"
        elif self.current <= -self.thresholds.pack_oc_discharge_warning:
            faults["pack_oc_discharge_warn"] = "WARNING"

        # ===== Temperature Faults =====
        if self.temperature >= self.thresholds.temp_critical:
            faults["overtemp_critical"] = "CRITICAL"
        elif self.temperature >= self.thresholds.temp_warning:
            faults["overtemp_warning"] = "WARNING"

        # ===== SOC Faults =====
        if self.soc <= self.thresholds.soc_low_warning:
            faults["soc_low"] = "WARNING"

        return faults

    def _update_state_machine(self) -> None:
        """
        Update system state based on active faults.

        State machine logic:
          NORMAL → WARNING (if any WARNING faults)
          WARNING / NORMAL → CRITICAL (if any CRITICAL faults)
          CRITICAL → LATCHED_FAULT (fault persists, latch on)
          LATCHED_FAULT / CRITICAL → SHUTDOWN (shutdown signal active)
        """
        has_critical = any(s == "CRITICAL" for s in self.active_faults.values())
        has_warning = any(s == "WARNING" for s in self.active_faults.values())

        # Determine new state
        if has_critical:
            self.system_state = SystemState.CRITICAL
            self.latched_fault = True
        elif self.latched_fault:
            self.system_state = SystemState.LATCHED_FAULT
        elif has_warning:
            self.system_state = SystemState.WARNING
        else:
            # No faults; can only recover from WARNING
            if self.system_state in (SystemState.NORMAL, SystemState.WARNING):
                self.system_state = SystemState.NORMAL
            # LATCHED_FAULT persists until explicit reset

    def update(self, dt_s: float = 1.0) -> BMSState:
        """
        Update BMS state machine and return current state.

        Args:
            dt_s: Time delta for this update (seconds)

        Returns:
            BMSState: Current system state and fault info
        """
        # Update internal models
        self._update_soc(dt_s)

        # Evaluate faults
        self.active_faults = self._check_faults()

        # Update state machine
        self._update_state_machine()

        # Generate shutdown signal (active-high when CRITICAL or LATCHED_FAULT)
        shutdown_signal = 1 if self.system_state in (SystemState.CRITICAL, SystemState.LATCHED_FAULT) else 0

        # Return state snapshot
        return BMSState(
            system_state=self.system_state,
            cells=self.cells.copy(),
            pack_voltage=sum(self.cells),
            current=self.current,
            temperature=self.temperature,
            soc=self.soc,
            faults=self.active_faults.copy(),
            shutdown_signal=shutdown_signal,
        )

    def get_state(self) -> Dict:
        """Get current state as a dictionary (for JSON/serial output)."""
        state = self.update()
        return {
            "system_state": state.system_state.name,
            "cells": state.cells,
            "pack_voltage_v": round(state.pack_voltage, 2),
            "current_a": round(state.current, 2),
            "temperature_c": round(state.temperature, 2),
            "soc_percent": round(state.soc, 1),
            "faults": state.faults,
            "shutdown_signal": state.shutdown_signal,
            "timestamp_ms": state.timestamp_ms,
        }

    def reset_latch(self) -> None:
        """Manually reset latched fault state (for testing)."""
        self.latched_fault = False
        self.system_state = SystemState.NORMAL
        self.active_faults.clear()

    def set_thresholds(self, thresholds: FaultThresholds) -> None:
        """Update fault thresholds dynamically."""
        self.thresholds = thresholds


# ============================================================================
# Convenience Functions
# ============================================================================

def create_lipo_3s(capacity_mah: int = 2500) -> BMSSimulator:
    """Create a 3S LiPo battery BMS (typical RC/quadcopter/robotics)."""
    return BMSSimulator(chemistry="lipo", num_cells=3, capacity_mah=capacity_mah)


def create_lifepo4_4s(capacity_mah: int = 5000) -> BMSSimulator:
    """Create a 4S LiFePO4 battery BMS (safer, longer cycle life)."""
    return BMSSimulator(chemistry="lifepo4", num_cells=4, capacity_mah=capacity_mah)


# ============================================================================
# Example Usage (for testing)
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("RaceCAN BMS Simulator — Day 19 Fault State Machine Demo")
    print("=" * 80)
    print()

    # Create a 3S LiPo BMS
    bms = create_lipo_3s(capacity_mah=2500)

    print("[Scenario 1] Normal operation")
    bms.update_cells([3.75, 3.70, 3.72])
    bms.update_current(5.0)
    bms.update_temperature(45.0)
    state = bms.get_state()
    print(f"  State: {state['system_state']}, Pack: {state['pack_voltage_v']}V, SOC: {state['soc_percent']}%")
    print(f"  Faults: {state['faults']}, Shutdown: {state['shutdown_signal']}")
    print()

    print("[Scenario 2] Cell overvoltage warning (cell 0 = 4.18V)")
    bms.update_cells([4.18, 3.70, 3.72])
    state = bms.get_state()
    print(f"  State: {state['system_state']}, Pack: {state['pack_voltage_v']}V")
    print(f"  Faults: {state['faults']}, Shutdown: {state['shutdown_signal']}")
    print()

    print("[Scenario 3] Cell overvoltage critical (cell 0 = 4.28V)")
    bms.update_cells([4.28, 3.70, 3.72])
    state = bms.get_state()
    print(f"  State: {state['system_state']}, Pack: {state['pack_voltage_v']}V")
    print(f"  Faults: {state['faults']}, Shutdown: {state['shutdown_signal']}")
    print()

    print("[Scenario 4] Pack overcurrent charge critical (20.5A)")
    bms.update_cells([3.75, 3.70, 3.72])
    bms.update_current(20.5)
    state = bms.get_state()
    print(f"  State: {state['system_state']}")
    print(f"  Faults: {state['faults']}, Shutdown: {state['shutdown_signal']}")
    print()

    print("[Scenario 5] Overtemperature critical (62°C)")
    bms.update_current(5.0)
    bms.update_temperature(62.0)
    state = bms.get_state()
    print(f"  State: {state['system_state']}")
    print(f"  Faults: {state['faults']}, Shutdown: {state['shutdown_signal']}")
    print()

    print("[Scenario 6] Fault recovery attempt (values back to normal)")
    bms.update_cells([3.75, 3.70, 3.72])
    bms.update_temperature(45.0)
    state = bms.get_state()
    print(f"  State: {state['system_state']} (still LATCHED until reset)")
    print(f"  Shutdown: {state['shutdown_signal']}")
    print()

    print("[Scenario 7] Manual reset of latched fault")
    bms.reset_latch()
    state = bms.get_state()
    print(f"  State: {state['system_state']} (reset to NORMAL)")
    print(f"  Shutdown: {state['shutdown_signal']}")
    print()

    print("=" * 80)
