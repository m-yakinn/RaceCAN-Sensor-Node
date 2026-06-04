# Sensor Input Design

This document explains the planned sensor input circuits for the RaceCAN sensor node.

## Purpose

The sensor input circuits convert real-world vehicle style signals into safe microcontroller inputs.

The first hardware design will include analog inputs for voltage, temperature, throttle, brake, and current.

## Battery Voltage Input

The battery voltage input uses a resistor divider to scale a higher voltage down to a safe ADC voltage.

Example:

```text
VIN ---- R1 ---- ADC_PIN ---- R2 ---- GND
``` 
# Sensor Input Design

This document explains the planned sensor input circuits for the RaceCAN sensor node.

## Purpose

The sensor input circuits convert real-world vehicle style signals into safe microcontroller inputs.

The first hardware design will include analog inputs for voltage, temperature, throttle, brake, and current.

## Battery Voltage Input

The battery voltage input uses a resistor divider to scale a higher voltage down to a safe ADC voltage.

Example:

```text
VIN ---- R1 ---- ADC_PIN ---- R2 ---- GND
```

Example resistor values:

| Resistor | Value |
|---|---:|
| R1 | 30k |
| R2 | 10k |

This creates a divide-by-4 ratio.

Example:

```text
12 V input becomes 3 V at the ADC pin
```

## Thermistor Temperature Input

The thermistor input uses a voltage divider.

Example:

```text
5V ---- Fixed Resistor ---- ADC_PIN ---- Thermistor ---- GND
```

As temperature changes, thermistor resistance changes, which changes the ADC voltage.

The firmware can convert the ADC value into temperature using:

1. Lookup table
2. Steinhart-Hart equation
3. Simplified beta equation

## Throttle and Brake Inputs

Throttle and brake inputs are modeled as analog percentage signals.

A potentiometer-style sensor can be represented as:

```text
5V ---- Sensor ---- GND
              |
              v
            ADC_PIN
```

The firmware converts ADC value into percent.

Example:

```text
0 ADC = 0 percent
1023 ADC = 100 percent
```

## Current Sensor Input

The current sensor input is modeled as an analog voltage from a current sensor module.

The firmware converts ADC voltage into current using the sensor sensitivity.

Example:

```text
ADC voltage -> current in amps
```

## Input Protection Ideas

Future PCB versions may include:

1. Series resistors
2. RC low-pass filters
3. Clamp diodes
4. TVS diodes
5. Input current limiting
6. Connector polarity labeling

## Filtering

Analog signals may be noisy, so future firmware may use:

1. Moving average filter
2. Exponential smoothing
3. Median filter
4. Simple threshold hysteresis

## Design Goal

Each sensor input should be:

1. Safe for the microcontroller
2. Easy to test
3. Clearly labeled
4. Documented with expected voltage range
5. Connected to a firmware conversion function
