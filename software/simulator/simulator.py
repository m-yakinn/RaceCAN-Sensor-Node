# RaceCAN Digital Kit
# Basic telemetry simulator with command line options

import argparse
import random
import time
import json

from config import NODE_ID, SIMULATION_DELAY_SECONDS
from fault_logic import check_faults
from message_encoder import encode_messages


VALID_MODES = ["normal", "warning", "fault"]


def generate_normal_telemetry(timestamp):
    return {
        "timestamp": timestamp,
        "node_id": NODE_ID,
        "battery_voltage": round(random.uniform(11.5, 12.6), 2),
        "temperature_c": round(random.uniform(25.0, 45.0), 2),
        "throttle_percent": round(random.uniform(0.0, 90.0), 2),
        "brake_percent": round(random.uniform(0.0, 80.0), 2),
        "current_a": round(random.uniform(0.0, 10.0), 2),
        "external_fault": False,
    }


def generate_warning_telemetry(timestamp):
    return {
        "timestamp": timestamp,
        "node_id": NODE_ID,
        "battery_voltage": round(random.uniform(10.6, 11.0), 2),
        "temperature_c": round(random.uniform(50.0, 59.0), 2),
        "throttle_percent": round(random.uniform(0.0, 90.0), 2),
        "brake_percent": round(random.uniform(0.0, 80.0), 2),
        "current_a": round(random.uniform(12.0, 14.5), 2),
        "external_fault": False,
    }


def generate_fault_telemetry(timestamp):
    fault_type = random.choice(["voltage", "temperature", "current", "external"])

    telemetry = generate_normal_telemetry(timestamp)

    if fault_type == "voltage":
        telemetry["battery_voltage"] = round(random.uniform(9.5, 10.4), 2)
    elif fault_type == "temperature":
        telemetry["temperature_c"] = round(random.uniform(61.0, 80.0), 2)
    elif fault_type == "current":
        telemetry["current_a"] = round(random.uniform(15.5, 25.0), 2)
    elif fault_type == "external":
        telemetry["external_fault"] = True

    return telemetry


def generate_telemetry(timestamp, mode):
    if mode == "normal":
        return generate_normal_telemetry(timestamp)
    if mode == "warning":
        return generate_warning_telemetry(timestamp)
    if mode == "fault":
        return generate_fault_telemetry(timestamp)

    return generate_normal_telemetry(timestamp)


def run_simulator(mode, cycles):
    print("RaceCAN Digital Kit Simulator")
    print(f"Mode: {mode}")

    if cycles is None:
        print("Cycles: continuous")
    else:
        print(f"Cycles: {cycles}")

    print("Press Ctrl+C to stop.\n")

    start_time = time.time()
    cycle_count = 0

    try:
        while True:
            if cycles is not None and cycle_count >= cycles:
                print("\nSimulator completed requested cycles.")
                break

            timestamp = time.time() - start_time

            telemetry = generate_telemetry(timestamp, mode)
            faults, system_state = check_faults(telemetry)

            telemetry["system_state"] = system_state

            messages = encode_messages(telemetry, faults)

            for message in messages:
                print(json.dumps(message, indent=2))

            print("-" * 60)

            cycle_count += 1
            time.sleep(SIMULATION_DELAY_SECONDS)

    except KeyboardInterrupt:
        print("\nSimulator stopped.")


def get_mode_interactively():
    print("Select simulation mode:")
    print("1. normal")
    print("2. warning")
    print("3. fault")

    choice = input("Enter choice: ").strip()

    if choice == "1":
        return "normal"
    if choice == "2":
        return "warning"
    if choice == "3":
        return "fault"

    print("Invalid choice. Defaulting to normal mode.")
    return "normal"


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="RaceCAN Digital Kit telemetry simulator"
    )

    parser.add_argument(
        "--mode",
        choices=VALID_MODES,
        help="Simulation mode: normal, warning, or fault",
    )

    parser.add_argument(
        "--cycles",
        type=int,
        help="Number of telemetry cycles to run. Leave blank for continuous mode.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    if args.mode is None:
        selected_mode = get_mode_interactively()
    else:
        selected_mode = args.mode

    run_simulator(selected_mode, args.cycles)
