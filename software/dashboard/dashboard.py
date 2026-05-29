# RaceCAN Digital Kit
# Terminal dashboard for simulated telemetry

import os
import sys
import time


# Allows dashboard.py to import files from software/simulator
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


def print_dashboard(telemetry, faults, messages):
    clear_terminal()

    print("RaceCAN Digital Kit Live Dashboard")
    print("=" * 45)
    print()
    print(f"Timestamp:       {round(telemetry['timestamp'], 2)} s")
    print(f"Node ID:         {telemetry['node_id']}")
    print()
    print(f"Battery Voltage: {telemetry['battery_voltage']} V")
    print(f"Temperature:     {telemetry['temperature_c']} C")
    print(f"Throttle:        {telemetry['throttle_percent']}%")
    print(f"Brake:           {telemetry['brake_percent']}%")
    print(f"Current:         {telemetry['current_a']} A")
    print()
    print(f"System State:    {telemetry['system_state']}")
    print(f"Active Faults:   {get_active_faults(faults)}")
    print()
    print("Recent CAN Style Messages")
    print("-" * 45)

    for message in messages:
        print(f"{message['can_id']} | {message['name']} | {message['data']}")

    print()
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
        print("\nDashboard stopped.")
        print("Telemetry log saved to racecan_log.csv")


if __name__ == "__main__":
    print("Select dashboard simulation mode:")
    print("1. normal")
    print("2. warning")
    print("3. fault")

    choice = input("Enter choice: ").strip()

    if choice == "1":
        selected_mode = "normal"
    elif choice == "2":
        selected_mode = "warning"
    elif choice == "3":
        selected_mode = "fault"
    else:
        print("Invalid choice. Defaulting to normal mode.")
        selected_mode = "normal"

    run_dashboard(selected_mode)
