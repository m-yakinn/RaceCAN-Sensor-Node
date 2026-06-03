# Firmware Architecture

This document explains the firmware architecture for the RaceCAN Digital Kit.

## Purpose

The firmware layer models how a low voltage sensor node would run on a microcontroller.

The firmware is responsible for reading sensors, converting raw values, checking faults, sending CAN messages, and controlling outputs.

## Main Firmware Responsibilities

1. Initialize pins and communication
2. Read analog and digital sensor inputs
3. Convert raw sensor values into engineering units
4. Detect warnings and critical faults
5. Update status LEDs and shutdown output
6. Format CAN style messages
7. Send telemetry messages at fixed intervals
8. Print debug data for development

## Firmware Data Flow

```text
Sensor Inputs
        ↓
Analog to Engineering Unit Conversion
        ↓
Fault Detection Logic
        ↓
System State Decision
        ↓
CAN Message Formatting
        ↓
CAN Transmission
        ↓
Dashboard or Receiver Node
