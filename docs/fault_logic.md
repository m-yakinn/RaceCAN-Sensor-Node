# Fault Logic

RaceCAN Digital Kit V1 includes fault detection logic to model safety critical low voltage systems.

## Fault Table

| Fault | Trigger Condition | System Response |
|---|---|---|
| Undervoltage | Battery voltage below 10.5 V | Set undervoltage fault flag |
| Voltage warning | Battery voltage below 11.0 V | Set voltage warning flag |
| Overtemperature | Temperature above 60 C | Set overtemperature fault flag |
| Temperature warning | Temperature above 50 C | Set temperature warning flag |
| Overcurrent | Current draw above 15 A | Set overcurrent fault flag |
| Current warning | Current draw above 12 A | Set current warning flag |
| Throttle range fault | Throttle below 2 percent or above 98 percent | Set sensor range fault flag |
| Brake range fault | Brake below 2 percent or above 98 percent | Set sensor range fault flag |
| External fault | Digital fault input active | Set external fault flag |
| Communication fault | No heartbeat received for 1 second | Set communication fault flag |

## Fault Priority

Critical faults:

1. Undervoltage
2. Overtemperature
3. Overcurrent
4. External fault
5. Communication fault

Warnings:

1. Voltage warning
2. Temperature warning
3. Current warning

## System Response

When a warning occurs, the dashboard should display a warning state.

When a critical fault occurs, the system should:

1. Set the matching fault flag
2. Mark the node status as faulted
3. Display the fault on the dashboard
4. Log the event to CSV
5. Simulate a shutdown output
