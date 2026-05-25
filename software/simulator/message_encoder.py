# RaceCAN Digital Kit
# CAN style message encoder

from config import (
    CAN_ID_HEARTBEAT,
    CAN_ID_VOLTAGE,
    CAN_ID_TEMPERATURE,
    CAN_ID_DRIVER_INPUTS,
    CAN_ID_CURRENT,
    CAN_ID_FAULTS,
)


def create_message(can_id, name, timestamp, data):
    return {
        "can_id": can_id,
        "name": name,
        "timestamp": round(timestamp, 2),
        "data": data,
    }


def encode_messages(telemetry, faults):
    timestamp = telemetry["timestamp"]

    messages = [
        create_message(
            CAN_ID_HEARTBEAT,
            "Heartbeat",
            timestamp,
            {
                "node_id": telemetry["node_id"],
                "system_state": telemetry["system_state"],
                "uptime_seconds": round(timestamp, 2),
            },
        ),
        create_message(
            CAN_ID_VOLTAGE,
            "Voltage Status",
            timestamp,
            {
                "battery_voltage": telemetry["battery_voltage"],
                "voltage_warning": faults["voltage_warning"],
                "undervoltage_fault": faults["undervoltage_fault"],
            },
        ),
        create_message(
            CAN_ID_TEMPERATURE,
            "Temperature Status",
            timestamp,
            {
                "temperature_c": telemetry["temperature_c"],
                "temperature_warning": faults["temperature_warning"],
                "overtemperature_fault": faults["overtemperature_fault"],
            },
        ),
        create_message(
            CAN_ID_DRIVER_INPUTS,
            "Driver Inputs",
            timestamp,
            {
                "throttle_percent": telemetry["throttle_percent"],
                "brake_percent": telemetry["brake_percent"],
                "sensor_range_fault": faults["sensor_range_fault"],
            },
        ),
        create_message(
            CAN_ID_CURRENT,
            "Current Status",
            timestamp,
            {
                "current_a": telemetry["current_a"],
                "current_warning": faults["current_warning"],
                "overcurrent_fault": faults["overcurrent_fault"],
            },
        ),
        create_message(
            CAN_ID_FAULTS,
            "Fault Status",
            timestamp,
            faults,
        ),
    ]

    return messages
