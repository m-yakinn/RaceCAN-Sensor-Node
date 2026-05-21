# Fault Logic

RaceCAN Sensor Node V1 will detect the following fault conditions:

| Fault | Trigger Condition | System Response |
|---|---|---|
| Undervoltage | Battery voltage below 10.5 V | Turn on fault LED and set fault flag |
| Overtemperature | Temperature above 60 C | Turn on fault LED and set fault flag |
| Sensor range fault | Throttle input below 2 percent or above 98 percent | Turn on fault LED and set fault flag |
| External fault | Digital fault input active | Turn on fault LED and set fault flag |
| CAN heartbeat fault | No heartbeat received for 1 second | Set communication fault flag |
