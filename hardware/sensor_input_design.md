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
