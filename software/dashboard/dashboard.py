# RaceCAN Digital Kit
# Terminal dashboard for simulated telemetry

import os
import sys
import time


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SOFTWARE_DIR = os.path.dirname(CURRENT_DIR)
SIMULATOR_DIR = os.path.join(SOFTWARE_DIR, "simulator")

sys.path.append(SIMULATOR_DIR)


from simulator import generate_telemetry
from fault_logic import check_faults
from message_encoder import encode_messages
from config import SIMULATION_DELAY_SECONDS
from csv_logger import log_telemetry, get_active_faults


def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")


def format_state(system_state):
    if system_state == "NORMAL":
        return "NORMAL"
    if system_state == "WARNING":
        return "WARNING"
    if system_state == "FAULT":
        return "FAULT"
    return system_state


def print_dashboard(telemetry, faults, messages):
    clear_terminal()

    active_faults = get_active_faults(faults)

    print("RaceCAN Digital Kit Live Dashboard")
    print("=" * 55)
    print()
    print("System Summary")
    print("-" * 55)
    print(f"Timestamp:        {round(telemetry['timestamp'], 2)} s")
    print(f"Node ID:          {telemetry['node_id']}")
    print(f"System State:     {format_state(telemetry['system_state'])}")
    print(f"Active Faults:    {active_faults}")
    print()
    print("Live Telemetry")
    print("-" * 55)
    print(f"Battery Voltage:  {telemetry['battery_voltage']} V")
    print(f"Temperature:      {telemetry['temperature_c']} C")
    print(f"Throttle:         {telemetry['throttle_percent']} percent")
    print(f"Brake:            {telemetry['brake_percent']} percent")
    print(f"Current Draw:     {telemetry['current_a']} A")
    print()
    print("Recent CAN Style Messages")
    print("-" * 55)

    for message in messages:
        print(f"{message['can_id']}  {message['name']}")

    print()
    print("Telemetry is being saved to racecan_log.csv")
    print("Press Ctrl+C to stop.")


def run_dashboard(mode):
    print("Starting RaceCAN dashboard...")
    time.sleep(1)

    start_time = time.time()

    try:
        while True:
            timestamp = time.time() - start_time

            telemetry = generate_telemetry(timestamp, mode)
            faults, system_state = check_faults(telemetry)

            telemetry["system_state"] = system_state

            messages = encode_messages(telemetry, faults)

            print_dashboard(telemetry, faults, messages)
            log_telemetry(telemetry, faults)

            time.sleep(SIMULATION_DELAY_SECONDS)

    except KeyboardInterrupt:
        print()
        print("Dashboard stopped.")
        print("Telemetry log saved to racecan_log.csv")


def get_mode_from_user():
    print("Select dashboard simulation mode:")
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


if __name__ == "__main__":
    selected_mode = get_mode_from_user()
    run_dashboard(selected_mode)
