# RaceCAN Digital Kit
# Fault detection logic

from config import (
    VOLTAGE_WARNING_THRESHOLD,
    TEMPERATURE_WARNING_THRESHOLD,
    CURRENT_WARNING_THRESHOLD,
    UNDERVOLTAGE_FAULT_THRESHOLD,
    OVERTEMPERATURE_FAULT_THRESHOLD,
    OVERCURRENT_FAULT_THRESHOLD,
    MIN_SENSOR_PERCENT,
    MAX_SENSOR_PERCENT,
)


def check_faults(telemetry):
    battery_voltage = telemetry["battery_voltage"]
    temperature_c = telemetry["temperature_c"]
    throttle_percent = telemetry["throttle_percent"]
    brake_percent = telemetry["brake_percent"]
    current_a = telemetry["current_a"]
    external_fault = telemetry["external_fault"]

    voltage_warning = battery_voltage < VOLTAGE_WARNING_THRESHOLD
    undervoltage_fault = battery_voltage < UNDERVOLTAGE_FAULT_THRESHOLD

    temperature_warning = temperature_c > TEMPERATURE_WARNING_THRESHOLD
    overtemperature_fault = temperature_c > OVERTEMPERATURE_FAULT_THRESHOLD

    current_warning = current_a > CURRENT_WARNING_THRESHOLD
    overcurrent_fault = current_a > OVERCURRENT_FAULT_THRESHOLD

    sensor_range_fault = (
        throttle_percent < MIN_SENSOR_PERCENT
        or throttle_percent > MAX_SENSOR_PERCENT
        or brake_percent < MIN_SENSOR_PERCENT
        or brake_percent > MAX_SENSOR_PERCENT
    )

    communication_fault = False

    faults = {
        "voltage_warning": voltage_warning,
        "undervoltage_fault": undervoltage_fault,
        "temperature_warning": temperature_warning,
        "overtemperature_fault": overtemperature_fault,
        "current_warning": current_warning,
        "overcurrent_fault": overcurrent_fault,
        "sensor_range_fault": sensor_range_fault,
        "external_fault": external_fault,
        "communication_fault": communication_fault,
    }

    critical_faults = [
        undervoltage_fault,
        overtemperature_fault,
        overcurrent_fault,
        sensor_range_fault,
        external_fault,
        communication_fault,
    ]

    warnings = [
        voltage_warning,
        temperature_warning,
        current_warning,
    ]

    if any(critical_faults):
        system_state = "FAULT"
    elif any(warnings):
        system_state = "WARNING"
    else:
        system_state = "NORMAL"

    return faults, system_state
