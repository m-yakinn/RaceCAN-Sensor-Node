# RaceCAN V1 CAN Protocol

This document defines the CAN style message structure for RaceCAN Digital Kit V1.

## Message Table

| CAN ID | Message Name | Purpose | Update Rate |
|---|---|---|---|
| 0x100 | Heartbeat | Confirms that the node is alive | 500 ms |
| 0x101 | Voltage Status | Sends battery voltage | 100 ms |
| 0x102 | Temperature Status | Sends temperature data | 100 ms |
| 0x103 | Driver Inputs | Sends throttle and brake position | 50 ms |
| 0x104 | Current Status | Sends current draw | 100 ms |
| 0x105 | Fault Status | Sends active fault flags | On change and every 500 ms |

## Message Details

### 0x100 Heartbeat

Fields:

1. Node ID
2. System state
3. Uptime

### 0x101 Voltage Status

Fields:

1. Battery voltage
2. Low voltage warning flag
3. Undervoltage fault flag

### 0x102 Temperature Status

Fields:

1. Temperature
2. Temperature warning flag
3. Overtemperature fault flag

### 0x103 Driver Inputs

Fields:

1. Throttle percent
2. Brake percent
3. Sensor range fault flag

### 0x104 Current Status

Fields:

1. Current draw
2. Overcurrent warning flag
3. Overcurrent fault flag

### 0x105 Fault Status

Fields:

1. Undervoltage fault
2. Overtemperature fault
3. Overcurrent fault
4. Sensor range fault
5. External fault
6. Communication fault
