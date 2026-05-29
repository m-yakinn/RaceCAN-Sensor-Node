# RaceCAN Digital Kit
# CSV logging helper for telemetry dashboard

import csv
import os


LOG_FILE_PATH = "racecan_log.csv"


def create_log_file():
    file_exists = os.path.exists(LOG_FILE_PATH)

    if not file_exists:
        with open(LOG_FILE_PATH, mode="w", newline="") as file:
            writer = csv.writer(file)

            writer.writerow([
                "timestamp",
                "node_id",
                "battery_voltage",
                "temperature_c",
                "throttle_percent",
                "brake_percent",
                "current_a",
                "system_state",
                "active_faults",
            ])


def get_active_faults(faults):
    active_faults = []

    for fault_name, is_active in faults.items():
        if is_active:
            active_faults.append(fault_name)

    if len(active_faults) == 0:
        return "NONE"

    return "|".join(active_faults)


def log_telemetry(telemetry, faults):
    create_log_file()

    with open(LOG_FILE_PATH, mode="a", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            round(telemetry["timestamp"], 2),
            telemetry["node_id"],
            telemetry["battery_voltage"],
            telemetry["temperature_c"],
            telemetry["throttle_percent"],
            telemetry["brake_percent"],
            telemetry["current_a"],
            telemetry["system_state"],
            get_active_faults(faults),
        ])
