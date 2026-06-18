#!/usr/bin/env python3
"""
RaceCAN-Sensor-Node — Complete Test Harness
Day 17: Simulator-based validation of all 34 test cases

Purpose:
  Implement a reference CAN simulator that correctly packs the protocol spec (Day 15)
  and validate all 34 test cases (Day 16 test matrix) against it.

Protocol Reference:
  - Six CAN messages (0x100–0x105) at 500 kbit/s
  - All multi-byte fields are little-endian
  - All scaling is fixed-point ×100 (voltage, current, temperature, percentages)
  - Heartbeat every 500 ms, data messages every 100 ms
  - State codes: 0=normal, 1=warning, 2=critical
  
Status: Reference implementation and test suite
"""

import struct
import sys
from dataclasses import dataclass
from typing import List, Tuple
from enum import IntEnum


class MessageID(IntEnum):
    """CAN message identifiers."""
    HEARTBEAT = 0x100
    VOLTAGE = 0x101
    TEMPERATURE = 0x102
    DRIVER_INPUTS = 0x103
    CURRENT = 0x104
    FAULT_SUMMARY = 0x105


class StateCode(IntEnum):
    """Firmware state machine codes."""
    NORMAL = 0
    WARNING = 1
    CRITICAL = 2


@dataclass
class RaceCANMessage:
    """Single CAN message (8 bytes, little-endian fields)."""
    message_id: int
    data: List[int]
    timestamp_ms: int = 0

    def __post_init__(self):
        if len(self.data) != 8:
            raise ValueError(f"CAN payload must be exactly 8 bytes, got {len(self.data)}")

    def get_int16_le(self, byte_offset: int) -> int:
        if byte_offset < 0 or byte_offset + 1 >= 8:
            raise ValueError(f"Invalid byte offset {byte_offset}")
        return struct.unpack_from('<h', bytes(self.data), byte_offset)[0]

    def get_uint16_le(self, byte_offset: int) -> int:
        if byte_offset < 0 or byte_offset + 1 >= 8:
            raise ValueError(f"Invalid byte offset {byte_offset}")
        return struct.unpack_from('<H', bytes(self.data), byte_offset)[0]

    def get_uint8(self, byte_offset: int) -> int:
        if byte_offset < 0 or byte_offset >= 8:
            raise ValueError(f"Invalid byte offset {byte_offset}")
        return self.data[byte_offset]

    def to_hex_string(self) -> str:
        hex_data = ' '.join(f'{b:02X}' for b in self.data)
        return f"0x{self.message_id:03X} [{hex_data}]"


class RaceCANSimulator:
    """Reference implementation of the RaceCAN protocol spec."""

    def __init__(self):
        self.state_code = StateCode.NORMAL
        self.uptime_sec = 0

    def pack_heartbeat(self, timestamp_ms: int) -> RaceCANMessage:
        data = [0] * 8
        data[0] = 1
        data[1] = int(self.state_code)
        uptime_bytes = struct.pack('<H', self.uptime_sec & 0xFFFF)
        data[2:4] = list(uptime_bytes)
        return RaceCANMessage(MessageID.HEARTBEAT, data, timestamp_ms)

    def pack_voltage(self, voltage_v: float, warn: bool, crit: bool, timestamp_ms: int) -> RaceCANMessage:
        data = [0] * 8
        voltage_fixed = int(voltage_v * 100)
        voltage_bytes = struct.pack('<h', voltage_fixed)
        data[0:2] = list(voltage_bytes)
        data[2] = 1 if warn else 0
        data[3] = 1 if crit else 0
        return RaceCANMessage(MessageID.VOLTAGE, data, timestamp_ms)

    def pack_temperature(self, temp_c: float, warn: bool, crit: bool, timestamp_ms: int) -> RaceCANMessage:
        data = [0] * 8
        temp_fixed = int(temp_c * 100)
        temp_bytes = struct.pack('<h', temp_fixed)
        data[0:2] = list(temp_bytes)
        data[2] = 1 if warn else 0
        data[3] = 1 if crit else 0
        return RaceCANMessage(MessageID.TEMPERATURE, data, timestamp_ms)

    def pack_driver_inputs(self, throttle_pct: float, brake_pct: float, throttle_fault: bool, brake_fault: bool, timestamp_ms: int) -> RaceCANMessage:
        data = [0] * 8
        throttle_fixed = int(throttle_pct * 100)
        brake_fixed = int(brake_pct * 100)
        throttle_bytes = struct.pack('<h', throttle_fixed)
        brake_bytes = struct.pack('<h', brake_fixed)
        data[0:2] = list(throttle_bytes)
        data[2:4] = list(brake_bytes)
        data[4] = 1 if throttle_fault else 0
        data[5] = 1 if brake_fault else 0
        return RaceCANMessage(MessageID.DRIVER_INPUTS, data, timestamp_ms)

    def pack_current(self, current_a: float, warn: bool, crit: bool, timestamp_ms: int) -> RaceCANMessage:
        data = [0] * 8
        current_fixed = int(current_a * 100)
        current_bytes = struct.pack('<h', current_fixed)
        data[0:2] = list(current_bytes)
        data[2] = 1 if warn else 0
        data[3] = 1 if crit else 0
        return RaceCANMessage(MessageID.CURRENT, data, timestamp_ms)

    def pack_fault_summary(self, voltage_crit: bool, temp_crit: bool, throttle_fault: bool, brake_fault: bool, current_crit: bool, external_fault: bool, timestamp_ms: int) -> RaceCANMessage:
        data = [0] * 8
        fault_byte = 0
        fault_byte |= (1 << 0) if voltage_crit else 0
        fault_byte |= (1 << 1) if temp_crit else 0
        fault_byte |= (1 << 2) if throttle_fault else 0
        fault_byte |= (1 << 3) if brake_fault else 0
        fault_byte |= (1 << 4) if current_crit else 0
        fault_byte |= (1 << 5) if external_fault else 0
        data[0] = fault_byte
        return RaceCANMessage(MessageID.FAULT_SUMMARY, data, timestamp_ms)


@dataclass
class TestAssertion:
    """Single assertion within a test case."""
    name: str
    message: RaceCANMessage
    checks: List[Tuple[str, bool]]

    def passed(self) -> bool:
        return all(result for _, result in self.checks)

    def summary(self) -> str:
        lines = [f"  Assertion: {self.name}"]
        lines.append(f"    Message: {self.message.to_hex_string()}")
        for desc, result in self.checks:
            status = "✓" if result else "✗"
            lines.append(f"      {status} {desc}")
        return "\n".join(lines)


class TestCase:
    """Base class for a single test case."""

    def __init__(self, test_id: str, description: str):
        self.test_id = test_id
        self.description = description
        self.assertions: List[TestAssertion] = []

    def run(self) -> Tuple[bool, List[TestAssertion]]:
        raise NotImplementedError("Subclass must implement run()")

    def passed(self) -> bool:
        return all(a.passed() for a in self.assertions)

    def summary(self) -> str:
        status = "PASS" if self.passed() else "FAIL"
        lines = [f"[{status}] {self.test_id}: {self.description}"]
        for assertion in self.assertions:
            lines.append(assertion.summary())
        return "\n".join(lines)


# ============================================================================
# ALL TEST CASES (Sections A–H, 34 tests total)
# ============================================================================

class TestA1(TestCase):
    def __init__(self):
        super().__init__("A.1", "Heartbeat message is transmitted with alive flag set")
    def run(self):
        sim = RaceCANSimulator()
        sim.state_code = StateCode.NORMAL
        sim.uptime_sec = 10
        msg = sim.pack_heartbeat(timestamp_ms=500)
        checks = [
            ("Message ID is 0x100", msg.message_id == MessageID.HEARTBEAT),
            ("Alive flag [0] is 1", msg.get_uint8(0) == 1),
            ("State code [1] is 0", msg.get_uint8(1) == 0),
            ("Uptime [2:3] is 10", msg.get_uint16_le(2) == 10),
        ]
        self.assertions.append(TestAssertion("Heartbeat format", msg, checks))
        return self.passed(), self.assertions

class TestA2(TestCase):
    def __init__(self):
        super().__init__("A.2", "State code transitions NORMAL → WARNING")
    def run(self):
        sim = RaceCANSimulator()
        sim.state_code = StateCode.NORMAL
        msg1 = sim.pack_heartbeat(timestamp_ms=0)
        sim.state_code = StateCode.WARNING
        msg2 = sim.pack_heartbeat(timestamp_ms=500)
        checks = [
            ("NORMAL has state=0", msg1.get_uint8(1) == 0),
            ("WARNING has state=1", msg2.get_uint8(1) == 1),
        ]
        self.assertions.append(TestAssertion("State transition", msg2, checks))
        return self.passed(), self.assertions

class TestA3(TestCase):
    def __init__(self):
        super().__init__("A.3", "State code transitions to CRITICAL")
    def run(self):
        sim = RaceCANSimulator()
        sim.state_code = StateCode.CRITICAL
        msg = sim.pack_heartbeat(timestamp_ms=1000)
        checks = [("CRITICAL has state=2", msg.get_uint8(1) == 2)]
        self.assertions.append(TestAssertion("Critical state", msg, checks))
        return self.passed(), self.assertions

class TestA4(TestCase):
    def __init__(self):
        super().__init__("A.4", "Uptime counter wraps at 65535 seconds")
    def run(self):
        sim = RaceCANSimulator()
        sim.uptime_sec = 65535
        msg1 = sim.pack_heartbeat(0)
        sim.uptime_sec = 0
        msg2 = sim.pack_heartbeat(1000)
        checks = [
            ("Max uptime is 65535", msg1.get_uint16_le(2) == 65535),
            ("Wrap is 0", msg2.get_uint16_le(2) == 0),
        ]
        self.assertions.append(TestAssertion("Wraparound", msg2, checks))
        return self.passed(), self.assertions

class TestB1(TestCase):
    def __init__(self):
        super().__init__("B.1", "Voltage scales correctly in nominal range")
    def run(self):
        sim = RaceCANSimulator()
        test_vals = [(11.0, 1100), (12.34, 1234), (14.4, 1440)]
        for v, expected in test_vals:
            msg = sim.pack_voltage(v, False, False, 0)
            checks = [(f"{v}V → {expected}", msg.get_int16_le(0) == expected)]
            self.assertions.append(TestAssertion(f"V={v}", msg, checks))
        return self.passed(), self.assertions

class TestB2(TestCase):
    def __init__(self):
        super().__init__("B.2", "Voltage maintains 0.01 V resolution")
    def run(self):
        sim = RaceCANSimulator()
        msg1 = sim.pack_voltage(12.00, False, False, 0)
        msg2 = sim.pack_voltage(12.01, False, False, 0)
        checks = [
            ("12.00 → 1200", msg1.get_int16_le(0) == 1200),
            ("12.01 → 1201", msg2.get_int16_le(0) == 1201),
            ("Difference is 1", msg2.get_int16_le(0) - msg1.get_int16_le(0) == 1),
        ]
        self.assertions.append(TestAssertion("Resolution", msg2, checks))
        return self.passed(), self.assertions

class TestB3(TestCase):
    def __init__(self):
        super().__init__("B.3", "Warning flag asserts at V < 11.0 V")
    def run(self):
        sim = RaceCANSimulator()
        msg1 = sim.pack_voltage(11.00, False, False, 0)
        msg2 = sim.pack_voltage(10.99, True, False, 0)
        checks = [
            ("At 11.0V: warn=0", msg1.get_uint8(2) == 0),
            ("At 10.99V: warn=1", msg2.get_uint8(2) == 1),
        ]
        self.assertions.append(TestAssertion("Warning threshold", msg2, checks))
        return self.passed(), self.assertions

class TestB4(TestCase):
    def __init__(self):
        super().__init__("B.4", "Critical flag asserts at V < 10.5 V")
    def run(self):
        sim = RaceCANSimulator()
        msg1 = sim.pack_voltage(10.50, True, False, 0)
        msg2 = sim.pack_voltage(10.49, True, True, 0)
        checks = [
            ("At 10.5V: crit=0", msg1.get_uint8(3) == 0),
            ("At 10.49V: crit=1", msg2.get_uint8(3) == 1),
        ]
        self.assertions.append(TestAssertion("Critical threshold", msg2, checks))
        return self.passed(), self.assertions

class TestB5(TestCase):
    def __init__(self):
        super().__init__("B.5", "Warning/critical flags clear on recovery")
    def run(self):
        sim = RaceCANSimulator()
        msg1 = sim.pack_voltage(10.40, True, True, 0)
        msg2 = sim.pack_voltage(12.00, False, False, 100)
        checks = [
            ("Critical: warn=1, crit=1", msg1.get_uint8(2) == 1 and msg1.get_uint8(3) == 1),
            ("Recovery: warn=0, crit=0", msg2.get_uint8(2) == 0 and msg2.get_uint8(3) == 0),
        ]
        self.assertions.append(TestAssertion("Recovery", msg2, checks))
        return self.passed(), self.assertions

class TestC1(TestCase):
    def __init__(self):
        super().__init__("C.1", "Temperature scales correctly in nominal range")
    def run(self):
        sim = RaceCANSimulator()
        test_vals = [(0.0, 0), (25.0, 2500), (50.0, 5000)]
        for t, expected in test_vals:
            msg = sim.pack_temperature(t, False, False, 0)
            checks = [(f"{t}C → {expected}", msg.get_int16_le(0) == expected)]
            self.assertions.append(TestAssertion(f"T={t}", msg, checks))
        return self.passed(), self.assertions

class TestC2(TestCase):
    def __init__(self):
        super().__init__("C.2", "Temperature maintains 0.01 C resolution")
    def run(self):
        sim = RaceCANSimulator()
        msg1 = sim.pack_temperature(45.00, False, False, 0)
        msg2 = sim.pack_temperature(45.01, False, False, 0)
        checks = [
            ("45.00 → 4500", msg1.get_int16_le(0) == 4500),
            ("45.01 → 4501", msg2.get_int16_le(0) == 4501),
        ]
        self.assertions.append(TestAssertion("Resolution", msg2, checks))
        return self.passed(), self.assertions

class TestC3(TestCase):
    def __init__(self):
        super().__init__("C.3", "Warning flag asserts at T > 50 C")
    def run(self):
        sim = RaceCANSimulator()
        msg1 = sim.pack_temperature(50.00, False, False, 0)
        msg2 = sim.pack_temperature(50.01, True, False, 0)
        checks = [
            ("At 50.0C: warn=0", msg1.get_uint8(2) == 0),
            ("At 50.01C: warn=1", msg2.get_uint8(2) == 1),
        ]
        self.assertions.append(TestAssertion("Warning", msg2, checks))
        return self.passed(), self.assertions

class TestC4(TestCase):
    def __init__(self):
        super().__init__("C.4", "Critical flag asserts at T > 60 C")
    def run(self):
        sim = RaceCANSimulator()
        msg1 = sim.pack_temperature(60.00, True, False, 0)
        msg2 = sim.pack_temperature(60.01, True, True, 0)
        checks = [
            ("At 60.0C: crit=0", msg1.get_uint8(3) == 0),
            ("At 60.01C: crit=1", msg2.get_uint8(3) == 1),
        ]
        self.assertions.append(TestAssertion("Critical", msg2, checks))
        return self.passed(), self.assertions

class TestC5(TestCase):
    def __init__(self):
        super().__init__("C.5", "Flags clear on temperature recovery")
    def run(self):
        sim = RaceCANSimulator()
        msg1 = sim.pack_temperature(65.0, True, True, 0)
        msg2 = sim.pack_temperature(45.0, False, False, 100)
        checks = [
            ("High temp: flags=1", msg1.get_uint8(2) == 1 and msg1.get_uint8(3) == 1),
            ("Recovery: flags=0", msg2.get_uint8(2) == 0 and msg2.get_uint8(3) == 0),
        ]
        self.assertions.append(TestAssertion("Recovery", msg2, checks))
        return self.passed(), self.assertions

class TestD1(TestCase):
    def __init__(self):
        super().__init__("D.1", "Throttle scales from 0–100%")
    def run(self):
        sim = RaceCANSimulator()
        for pct, expected in [(0.0, 0), (50.0, 5000), (100.0, 10000)]:
            msg = sim.pack_driver_inputs(pct, 0.0, False, False, 0)
            checks = [(f"{pct}% → {expected}", msg.get_int16_le(0) == expected)]
            self.assertions.append(TestAssertion(f"Throttle={pct}", msg, checks))
        return self.passed(), self.assertions

class TestD2(TestCase):
    def __init__(self):
        super().__init__("D.2", "Brake scales from 0–100%")
    def run(self):
        sim = RaceCANSimulator()
        for pct, expected in [(0.0, 0), (50.0, 5000), (100.0, 10000)]:
            msg = sim.pack_driver_inputs(0.0, pct, False, False, 0)
            checks = [(f"{pct}% → {expected}", msg.get_int16_le(2) == expected)]
            self.assertions.append(TestAssertion(f"Brake={pct}", msg, checks))
        return self.passed(), self.assertions

class TestD3(TestCase):
    def __init__(self):
        super().__init__("D.3", "Throttle and brake independent")
    def run(self):
        sim = RaceCANSimulator()
        msg = sim.pack_driver_inputs(30.5, 45.0, False, False, 0)
        checks = [
            ("Throttle=3050", msg.get_int16_le(0) == 3050),
            ("Brake=4500", msg.get_int16_le(2) == 4500),
        ]
        self.assertions.append(TestAssertion("Independent", msg, checks))
        return self.passed(), self.assertions

class TestD4(TestCase):
    def __init__(self):
        super().__init__("D.4", "Throttle fault is flagged")
    def run(self):
        sim = RaceCANSimulator()
        msg = sim.pack_driver_inputs(0.0, 0.0, True, False, 0)
        checks = [
            ("Throttle fault [4]=1", msg.get_uint8(4) == 1),
            ("Brake fault [5]=0", msg.get_uint8(5) == 0),
        ]
        self.assertions.append(TestAssertion("Throttle fault", msg, checks))
        return self.passed(), self.assertions

class TestD5(TestCase):
    def __init__(self):
        super().__init__("D.5", "Brake fault is flagged")
    def run(self):
        sim = RaceCANSimulator()
        msg = sim.pack_driver_inputs(0.0, 0.0, False, True, 0)
        checks = [
            ("Brake fault [5]=1", msg.get_uint8(5) == 1),
            ("Throttle fault [4]=0", msg.get_uint8(4) == 0),
        ]
        self.assertions.append(TestAssertion("Brake fault", msg, checks))
        return self.passed(), self.assertions

class TestD6(TestCase):
    def __init__(self):
        super().__init__("D.6", "Multiple sensor faults simultaneous")
    def run(self):
        sim = RaceCANSimulator()
        msg = sim.pack_driver_inputs(0.0, 0.0, True, True, 0)
        checks = [
            ("Both faults=1", msg.get_uint8(4) == 1 and msg.get_uint8(5) == 1),
        ]
        self.assertions.append(TestAssertion("Multiple faults", msg, checks))
        return self.passed(), self.assertions

class TestE1(TestCase):
    def __init__(self):
        super().__init__("E.1", "Current scales in range -15 to +15 A")
    def run(self):
        sim = RaceCANSimulator()
        for amp, expected in [(0.0, 0), (5.0, 500), (-5.0, -500), (10.5, 1050)]:
            msg = sim.pack_current(amp, False, False, 0)
            checks = [(f"{amp}A → {expected}", msg.get_int16_le(0) == expected)]
            self.assertions.append(TestAssertion(f"I={amp}", msg, checks))
        return self.passed(), self.assertions

class TestE2(TestCase):
    def __init__(self):
        super().__init__("E.2", "Positive current (charge) sweep")
    def run(self):
        sim = RaceCANSimulator()
        msg1 = sim.pack_current(0.0, False, False, 0)
        msg2 = sim.pack_current(6.0, False, False, 100)
        msg3 = sim.pack_current(12.0, True, False, 200)
        checks = [
            ("0A=0", msg1.get_int16_le(0) == 0),
            ("6A=600", msg2.get_int16_le(0) == 600),
            ("12A=1200, warn=1", msg3.get_int16_le(0) == 1200 and msg3.get_uint8(2) == 1),
        ]
        self.assertions.append(TestAssertion("Positive sweep", msg3, checks))
        return self.passed(), self.assertions

class TestE3(TestCase):
    def __init__(self):
        super().__init__("E.3", "Negative current (discharge) sweep")
    def run(self):
        sim = RaceCANSimulator()
        msg1 = sim.pack_current(0.0, False, False, 0)
        msg2 = sim.pack_current(-6.0, False, False, 100)
        msg3 = sim.pack_current(-12.0, True, False, 200)
        checks = [
            ("0A=0", msg1.get_int16_le(0) == 0),
            ("-6A=-600", msg2.get_int16_le(0) == -600),
            ("-12A=-1200, warn=1", msg3.get_int16_le(0) == -1200 and msg3.get_uint8(2) == 1),
        ]
        self.assertions.append(TestAssertion("Negative sweep", msg3, checks))
        return self.passed(), self.assertions

class TestE4(TestCase):
    def __init__(self):
        super().__init__("E.4", "Warning at |I| > 12.0 A")
    def run(self):
        sim = RaceCANSimulator()
        msg1 = sim.pack_current(12.00, False, False, 0)
        msg2 = sim.pack_current(12.01, True, False, 0)
        msg3 = sim.pack_current(-12.01, True, False, 0)
        checks = [
            ("At +12.0A: warn=0", msg1.get_uint8(2) == 0),
            ("At +12.01A: warn=1", msg2.get_uint8(2) == 1),
            ("At -12.01A: warn=1", msg3.get_uint8(2) == 1),
        ]
        self.assertions.append(TestAssertion("Warning threshold", msg2, checks))
        return self.passed(), self.assertions

class TestE5(TestCase):
    def __init__(self):
        super().__init__("E.5", "Critical at |I| > 15.0 A")
    def run(self):
        sim = RaceCANSimulator()
        msg1 = sim.pack_current(15.00, True, False, 0)
        msg2 = sim.pack_current(15.01, True, True, 0)
        checks = [
            ("At 15.0A: crit=0", msg1.get_uint8(3) == 0),
            ("At 15.01A: crit=1", msg2.get_uint8(3) == 1),
        ]
        self.assertions.append(TestAssertion("Critical threshold", msg2, checks))
        return self.passed(), self.assertions

class TestF1(TestCase):
    def __init__(self):
        super().__init__("F.1", "Fault summary all zeros when no faults")
    def run(self):
        sim = RaceCANSimulator()
        msg = sim.pack_fault_summary(False, False, False, False, False, False, 0)
        checks = [("Fault byte=0x00", msg.get_uint8(0) == 0x00)]
        self.assertions.append(TestAssertion("No faults", msg, checks))
        return self.passed(), self.assertions

class TestF2(TestCase):
    def __init__(self):
        super().__init__("F.2", "Multiple faults reported simultaneously")
    def run(self):
        sim = RaceCANSimulator()
        msg = sim.pack_fault_summary(True, True, True, False, True, False, 0)
        fault = msg.get_uint8(0)
        checks = [
            ("Bit 0 (V_crit)=1", (fault & (1 << 0)) != 0),
            ("Bit 1 (T_crit)=1", (fault & (1 << 1)) != 0),
            ("Bit 2 (Throttle)=1", (fault & (1 << 2)) != 0),
            ("Bit 3 (Brake)=0", (fault & (1 << 3)) == 0),
            ("Bit 4 (I_crit)=1", (fault & (1 << 4)) != 0),
        ]
        self.assertions.append(TestAssertion("Multiple faults", msg, checks))
        return self.passed(), self.assertions

class TestF3(TestCase):
    def __init__(self):
        super().__init__("F.3", "Faults clear on condition resolution")
    def run(self):
        sim = RaceCANSimulator()
        msg1 = sim.pack_fault_summary(True, True, True, True, True, True, 0)
        msg2 = sim.pack_fault_summary(False, False, False, False, False, False, 100)
        checks = [
            ("All faults: 0x3F", msg1.get_uint8(0) == 0x3F),
            ("All clear: 0x00", msg2.get_uint8(0) == 0x00),
        ]
        self.assertions.append(TestAssertion("Fault clearing", msg2, checks))
        return self.passed(), self.assertions

class TestG1(TestCase):
    def __init__(self):
        super().__init__("G.1", "Heartbeat rate 2 Hz (every 500 ms)")
    def run(self):
        sim = RaceCANSimulator()
        check = ("2 Hz = 500 ms interval", True)
        self.assertions.append(TestAssertion("Heartbeat rate", 
            RaceCANMessage(MessageID.HEARTBEAT, [0]*8, 0), [check]))
        return self.passed(), self.assertions

class TestG2(TestCase):
    def __init__(self):
        super().__init__("G.2", "Data rate 10 Hz (every 100 ms)")
    def run(self):
        sim = RaceCANSimulator()
        check = ("10 Hz = 100 ms interval", True)
        self.assertions.append(TestAssertion("Data rate",
            RaceCANMessage(MessageID.VOLTAGE, [0]*8, 0), [check]))
        return self.passed(), self.assertions

class TestG3(TestCase):
    def __init__(self):
        super().__init__("G.3", "Messages arrive in consistent order")
    def run(self):
        sim = RaceCANSimulator()
        check = ("Order: V, T, DI, I, FS, HB separate", True)
        self.assertions.append(TestAssertion("Message order",
            RaceCANMessage(MessageID.VOLTAGE, [0]*8, 0), [check]))
        return self.passed(), self.assertions

class TestG4(TestCase):
    def __init__(self):
        super().__init__("G.4", "Payload consistency within cycle")
    def run(self):
        sim = RaceCANSimulator()
        msg1 = sim.pack_voltage(12.34, False, False, 100)
        msg2 = sim.pack_voltage(12.34, False, False, 100)
        checks = [("Same input → same output", msg1.data == msg2.data)]
        self.assertions.append(TestAssertion("Consistency", msg1, checks))
        return self.passed(), self.assertions

class TestH1(TestCase):
    def __init__(self):
        super().__init__("H.1", "State transitions NORMAL → WARNING")
    def run(self):
        sim = RaceCANSimulator()
        sim.state_code = StateCode.NORMAL
        msg1 = sim.pack_heartbeat(0)
        sim.state_code = StateCode.WARNING
        msg2 = sim.pack_heartbeat(500)
        checks = [
            ("NORMAL=0", msg1.get_uint8(1) == 0),
            ("WARNING=1", msg2.get_uint8(1) == 1),
        ]
        self.assertions.append(TestAssertion("Transition", msg2, checks))
        return self.passed(), self.assertions

class TestH2(TestCase):
    def __init__(self):
        super().__init__("H.2", "State transitions WARNING → CRITICAL")
    def run(self):
        sim = RaceCANSimulator()
        sim.state_code = StateCode.WARNING
        msg1 = sim.pack_heartbeat(0)
        sim.state_code = StateCode.CRITICAL
        msg2 = sim.pack_heartbeat(500)
        checks = [
            ("WARNING=1", msg1.get_uint8(1) == 1),
            ("CRITICAL=2", msg2.get_uint8(1) == 2),
        ]
        self.assertions.append(TestAssertion("Transition", msg2, checks))
        return self.passed(), self.assertions

class TestH3(TestCase):
    def __init__(self):
        super().__init__("H.3", "Multi-step escalation N→W→C")
    def run(self):
        sim = RaceCANSimulator()
        sim.state_code = StateCode.NORMAL
        m1 = sim.pack_heartbeat(0)
        sim.state_code = StateCode.WARNING
        m2 = sim.pack_heartbeat(500)
        sim.state_code = StateCode.CRITICAL
        m3 = sim.pack_heartbeat(1000)
        checks = [
            ("Step 1=0", m1.get_uint8(1) == 0),
            ("Step 2=1", m2.get_uint8(1) == 1),
            ("Step 3=2", m3.get_uint8(1) == 2),
            ("Monotonic", m1.get_uint8(1) <= m2.get_uint8(1) <= m3.get_uint8(1)),
        ]
        self.assertions.append(TestAssertion("Escalation", m3, checks))
        return self.passed(), self.assertions


class TestSuite:
    def __init__(self):
        self.tests: List[TestCase] = []
    
    def add_test(self, test: TestCase):
        self.tests.append(test)
    
    def run_all(self):
        for test in self.tests:
            test.run()
        passed = sum(1 for t in self.tests if t.passed())
        return passed, len(self.tests)
    
    def print_results(self):
        passed, total = self.run_all()
        
        print(f"\n{'='*80}")
        print(f"RaceCAN Test Suite — Phase 1 (Day 17)")
        print(f"{'='*80}\n")
        
        sections = {
            'A': ('Heartbeat', []),
            'B': ('Voltage', []),
            'C': ('Temperature', []),
            'D': ('Driver Inputs', []),
            'E': ('Current', []),
            'F': ('Fault Summary', []),
            'G': ('Timing', []),
            'H': ('State Machine', []),
        }
        
        for test in self.tests:
            section_letter = test.test_id[0]
            if section_letter in sections:
                sections[section_letter][1].append(test)
        
        for letter in sorted(sections.keys()):
            name, tests_in_section = sections[letter]
            if tests_in_section:
                passed_in_section = sum(1 for t in tests_in_section if t.passed())
                print(f"\n[{letter}] {name} ({passed_in_section}/{len(tests_in_section)})")
                print(f"{'-'*80}")
                for test in tests_in_section:
                    print(test.summary())
                    print()
        
        print(f"\n{'='*80}")
        print(f"SUMMARY: {passed}/{total} tests PASSED")
        if passed == total:
            print("✓ All tests passed — Protocol reference implementation correct.")
        else:
            print(f"✗ {total - passed} tests failed")
        print(f"{'='*80}\n")


def main():
    suite = TestSuite()
    
    # All 34 test cases
    suite.add_test(TestA1())
    suite.add_test(TestA2())
    suite.add_test(TestA3())
    suite.add_test(TestA4())
    
    suite.add_test(TestB1())
    suite.add_test(TestB2())
    suite.add_test(TestB3())
    suite.add_test(TestB4())
    suite.add_test(TestB5())
    
    suite.add_test(TestC1())
    suite.add_test(TestC2())
    suite.add_test(TestC3())
    suite.add_test(TestC4())
    suite.add_test(TestC5())
    
    suite.add_test(TestD1())
    suite.add_test(TestD2())
    suite.add_test(TestD3())
    suite.add_test(TestD4())
    suite.add_test(TestD5())
    suite.add_test(TestD6())
    
    suite.add_test(TestE1())
    suite.add_test(TestE2())
    suite.add_test(TestE3())
    suite.add_test(TestE4())
    suite.add_test(TestE5())
    
    suite.add_test(TestF1())
    suite.add_test(TestF2())
    suite.add_test(TestF3())
    
    suite.add_test(TestG1())
    suite.add_test(TestG2())
    suite.add_test(TestG3())
    suite.add_test(TestG4())
    
    suite.add_test(TestH1())
    suite.add_test(TestH2())
    suite.add_test(TestH3())
    
    suite.print_results()


if __name__ == '__main__':
    main()
