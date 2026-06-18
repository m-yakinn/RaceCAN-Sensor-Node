#!/usr/bin/env python3
"""
RaceCAN Dashboard Receiver (Python Implementation)
Day 18: Receiver-side telemetry parser and validator

Purpose:
  Demonstrates how a secondary ECU (dashboard, telemetry logger, BMS) would
  receive and unpack RaceCAN CAN messages. This is the Python equivalent
  of the C receiver, proving the protocol is implementable from both sides.

Usage:
  python3 dashboard_receiver.py [input_file.log]
  
  If input_file is a CAN log (one frame per line in format "ID DATA"),
  parse and display all messages.
  
Example input file format:
  100 01 00 0A 00 00 00 00 00
  101 D2 04 00 00 00 00 00 00
  102 95 11 00 00 00 00 00 00
  103 88 13 00 00 00 00 00 00
  104 B0 04 00 00 00 00 00 00
  105 00 00 00 00 00 00 00 00

Output:
  HEARTBEAT: State=0 (NORMAL), Uptime=10s
  VOLTAGE: 12.34V, Warn=0, Crit=0
  ...
"""

import struct
import sys
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class CANMessage:
    """Represents a single CAN frame."""
    msg_id: int
    dlc: int
    data: bytes
    timestamp_ms: float = 0.0
    
    def __repr__(self):
        data_hex = ' '.join(f'{b:02X}' for b in self.data)
        return f"ID=0x{self.msg_id:03X} DLC={self.dlc} [{data_hex}]"


class DashboardReceiver:
    """
    Reference receiver implementation that unpacks RaceCAN messages
    and validates them against the Day 15 protocol specification.
    """
    
    def __init__(self):
        self.messages_received = []
        self.state_history = []
        self.fault_timeline = []
        self.last_state = None
    
    # ========================================================================
    # Little-Endian Unpackers
    # ========================================================================
    
    @staticmethod
    def unpack_u16_le(data: bytes, offset: int) -> int:
        """Extract unsigned 16-bit little-endian integer."""
        low = data[offset]
        high = data[offset + 1]
        return low | (high << 8)
    
    @staticmethod
    def unpack_i16_le(data: bytes, offset: int) -> int:
        """Extract signed 16-bit little-endian integer (two's complement)."""
        val = DashboardReceiver.unpack_u16_le(data, offset)
        if val >= 0x8000:
            val -= 0x10000
        return val
    
    @staticmethod
    def unpack_u8(data: bytes, offset: int) -> int:
        """Extract unsigned 8-bit value."""
        return data[offset]
    
    # ========================================================================
    # Message Unpacking Functions
    # ========================================================================
    
    def unpack_heartbeat(self, msg: CANMessage) -> Dict:
        """
        Unpack 0x100 Heartbeat message.
        
        Payload:
          [0]   Alive flag (always 1)
          [1]   State code (0=normal, 1=warning, 2=critical)
          [2:3] Uptime in seconds (uint16 LE)
          [4:7] Reserved
        """
        alive = self.unpack_u8(msg.data, 0)
        state = self.unpack_u8(msg.data, 1)
        uptime_sec = self.unpack_u16_le(msg.data, 2)
        
        state_name = {0: 'NORMAL', 1: 'WARNING', 2: 'CRITICAL'}.get(state, 'UNKNOWN')
        
        result = {
            'type': 'HEARTBEAT',
            'alive': alive,
            'state': state,
            'state_name': state_name,
            'uptime_sec': uptime_sec,
        }
        
        # Track state transitions
        if self.last_state != state:
            self.state_history.append((msg.timestamp_ms, state_name))
            self.last_state = state
        
        return result
    
    def unpack_voltage(self, msg: CANMessage) -> Dict:
        """
        Unpack 0x101 Voltage Telemetry message.
        
        Payload:
          [0:1] Battery voltage (int16 LE, units: 0.01V)
          [2]   Voltage warning flag
          [3]   Voltage critical fault flag
          [4:7] Reserved
        """
        voltage_raw = self.unpack_i16_le(msg.data, 0)
        voltage_v = voltage_raw / 100.0
        warn = self.unpack_u8(msg.data, 2)
        crit = self.unpack_u8(msg.data, 3)
        
        return {
            'type': 'VOLTAGE',
            'voltage_raw': voltage_raw,
            'voltage_v': voltage_v,
            'warn': warn,
            'crit': crit,
        }
    
    def unpack_temperature(self, msg: CANMessage) -> Dict:
        """
        Unpack 0x102 Temperature Telemetry message.
        
        Payload:
          [0:1] Temperature (int16 LE, units: 0.01°C)
          [2]   Temperature warning flag
          [3]   Temperature critical fault flag
          [4:7] Reserved
        """
        temp_raw = self.unpack_i16_le(msg.data, 0)
        temp_c = temp_raw / 100.0
        warn = self.unpack_u8(msg.data, 2)
        crit = self.unpack_u8(msg.data, 3)
        
        return {
            'type': 'TEMPERATURE',
            'temperature_raw': temp_raw,
            'temperature_c': temp_c,
            'warn': warn,
            'crit': crit,
        }
    
    def unpack_driver_inputs(self, msg: CANMessage) -> Dict:
        """
        Unpack 0x103 Driver Inputs message.
        
        Payload:
          [0:1] Throttle position (int16 LE, units: 0.01%)
          [2:3] Brake position (int16 LE, units: 0.01%)
          [4]   Throttle sensor fault flag
          [5]   Brake sensor fault flag
          [6:7] Reserved
        """
        throttle_raw = self.unpack_i16_le(msg.data, 0)
        brake_raw = self.unpack_i16_le(msg.data, 2)
        throttle_pct = throttle_raw / 100.0
        brake_pct = brake_raw / 100.0
        throttle_fault = self.unpack_u8(msg.data, 4)
        brake_fault = self.unpack_u8(msg.data, 5)
        
        return {
            'type': 'DRIVER_INPUTS',
            'throttle_raw': throttle_raw,
            'throttle_pct': throttle_pct,
            'brake_raw': brake_raw,
            'brake_pct': brake_pct,
            'throttle_fault': throttle_fault,
            'brake_fault': brake_fault,
        }
    
    def unpack_current(self, msg: CANMessage) -> Dict:
        """
        Unpack 0x104 Current Telemetry message.
        
        Payload:
          [0:1] Pack current (int16 LE, units: 0.01A, signed)
          [2]   Current warning flag
          [3]   Current critical fault flag
          [4:7] Reserved
        """
        current_raw = self.unpack_i16_le(msg.data, 0)
        current_a = current_raw / 100.0
        warn = self.unpack_u8(msg.data, 2)
        crit = self.unpack_u8(msg.data, 3)
        
        return {
            'type': 'CURRENT',
            'current_raw': current_raw,
            'current_a': current_a,
            'warn': warn,
            'crit': crit,
        }
    
    def unpack_fault_summary(self, msg: CANMessage) -> Dict:
        """
        Unpack 0x105 Fault Summary message.
        
        Payload:
          [0] Bit 0–5: Fault flags (V_crit, T_crit, Throttle, Brake, I_crit, External)
          [0] Bit 6–7: Reserved
          [1:7] Reserved
        """
        fault_byte = self.unpack_u8(msg.data, 0)
        
        v_crit = (fault_byte >> 0) & 1
        t_crit = (fault_byte >> 1) & 1
        throttle = (fault_byte >> 2) & 1
        brake = (fault_byte >> 3) & 1
        i_crit = (fault_byte >> 4) & 1
        external = (fault_byte >> 5) & 1
        
        faults_present = v_crit or t_crit or throttle or brake or i_crit or external
        if faults_present:
            self.fault_timeline.append((msg.timestamp_ms, fault_byte))
        
        return {
            'type': 'FAULT_SUMMARY',
            'fault_byte': fault_byte,
            'v_crit': v_crit,
            't_crit': t_crit,
            'throttle': throttle,
            'brake': brake,
            'i_crit': i_crit,
            'external': external,
        }
    
    def process_message(self, msg: CANMessage) -> Optional[Dict]:
        """Route received message to appropriate unpacker."""
        if msg.msg_id == 0x100:
            result = self.unpack_heartbeat(msg)
        elif msg.msg_id == 0x101:
            result = self.unpack_voltage(msg)
        elif msg.msg_id == 0x102:
            result = self.unpack_temperature(msg)
        elif msg.msg_id == 0x103:
            result = self.unpack_driver_inputs(msg)
        elif msg.msg_id == 0x104:
            result = self.unpack_current(msg)
        elif msg.msg_id == 0x105:
            result = self.unpack_fault_summary(msg)
        else:
            print(f"Unknown message ID: 0x{msg.msg_id:03X}")
            return None
        
        self.messages_received.append(result)
        return result
    
    def print_message(self, result: Dict):
        """Pretty-print a parsed message."""
        msg_type = result['type']
        
        if msg_type == 'HEARTBEAT':
            print(f"HEARTBEAT: State={result['state']} ({result['state_name']}), "
                  f"Uptime={result['uptime_sec']}s")
        
        elif msg_type == 'VOLTAGE':
            print(f"VOLTAGE: {result['voltage_v']:.2f}V, "
                  f"Warn={result['warn']}, Crit={result['crit']}")
        
        elif msg_type == 'TEMPERATURE':
            print(f"TEMPERATURE: {result['temperature_c']:.2f}C, "
                  f"Warn={result['warn']}, Crit={result['crit']}")
        
        elif msg_type == 'DRIVER_INPUTS':
            print(f"DRIVER_INPUTS: Throttle={result['throttle_pct']:.1f}%, "
                  f"Brake={result['brake_pct']:.1f}%, "
                  f"ThrottleFault={result['throttle_fault']}, "
                  f"BrakeFault={result['brake_fault']}")
        
        elif msg_type == 'CURRENT':
            print(f"CURRENT: {result['current_a']:.2f}A, "
                  f"Warn={result['warn']}, Crit={result['crit']}")
        
        elif msg_type == 'FAULT_SUMMARY':
            faults = []
            if result['v_crit']: faults.append("V_crit")
            if result['t_crit']: faults.append("T_crit")
            if result['throttle']: faults.append("Throttle")
            if result['brake']: faults.append("Brake")
            if result['i_crit']: faults.append("I_crit")
            if result['external']: faults.append("External")
            
            if faults:
                print(f"FAULT_SUMMARY: {', '.join(faults)}")
            else:
                print("FAULT_SUMMARY: All clear")
    
    def print_summary(self):
        """Print end-of-session summary."""
        print("\n" + "="*80)
        print("DASHBOARD RECEIVER SUMMARY")
        print("="*80)
        print(f"Messages received: {len(self.messages_received)}")
        print(f"State transitions: {len(self.state_history)}")
        print(f"Fault events: {len(self.fault_timeline)}")
        
        if self.state_history:
            print("\nState history:")
            for timestamp, state in self.state_history:
                print(f"  {timestamp:.1f}ms: {state}")
        
        if self.fault_timeline:
            print("\nFault events:")
            for timestamp, fault_byte in self.fault_timeline:
                print(f"  {timestamp:.1f}ms: 0x{fault_byte:02X}")
        
        print("="*80)


def parse_can_log_line(line: str) -> Optional[CANMessage]:
    """Parse a line from a CAN log file (format: ID DATA)."""
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    
    parts = line.split()
    if len(parts) < 2:
        return None
    
    try:
        msg_id = int(parts[0], 16)
        data = bytes([int(b, 16) for b in parts[1:]])
        return CANMessage(msg_id, len(data), data)
    except ValueError:
        return None


def main():
    """Main entry point."""
    receiver = DashboardReceiver()
    
    # For demo: create some test messages
    test_messages = [
        CANMessage(0x100, 8, bytes([0x01, 0x00, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00])),
        CANMessage(0x101, 8, bytes([0xD2, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])),
        CANMessage(0x102, 8, bytes([0x95, 0x11, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])),
        CANMessage(0x103, 8, bytes([0x88, 0x13, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])),
        CANMessage(0x104, 8, bytes([0xB0, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])),
        CANMessage(0x105, 8, bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])),
    ]
    
    print("RaceCAN Dashboard Receiver\n")
    print("="*80)
    
    for msg in test_messages:
        result = receiver.process_message(msg)
        if result:
            receiver.print_message(result)
    
    receiver.print_summary()


if __name__ == '__main__':
    main()
