import csv
import numpy as np
import matplotlib.pyplot as plt

from tags.state_machine import StateSerializer
from main import load_json, load_txt  # or just load_json if using JSON files
from tags.tag import TagMode
from physics import PhysicsEngine 
from state import AppState

OUTPUT_CSV = "feedback_phase_sine.csv"
CONFIG_PATH = "demo/3_tag_test/config_files/config.json"

def run_feedback_phase_sweep():
    app_state = AppState()
    serializer = StateSerializer()

    # Load 3-tag test case config
    exciter, tags, _, _ = load_json(CONFIG_PATH, serializer, app_state=app_state)

    # Initialize physics engine
    physics_engine = PhysicsEngine(exciter, tags)

    tx1 = tags["TX1"]
    tx2 = tags["TX2"]
    rx = tags["RX1"]

    results = []

    num_modes_tx1 = len(tx1.chip_impedances)
    num_modes_tx2 = len(tx2.chip_impedances)

    for i in range(num_modes_tx1):
        tx1.set_mode(TagMode(i))  # Use the index as mode
        for j in range(num_modes_tx2):
            tx2.set_mode(TagMode(j))

            v_rx = physics_engine.voltage_at_tag(tags, rx)

            # Calculate total phase at RX from both transmitters
            sig1 = physics_engine.get_sig_tx_rx(tx1, rx)
            sig2 = physics_engine.get_sig_tx_rx(tx2, rx)
            total_sig = sig1 + sig2
            total_phase = np.angle(total_sig, deg=True)

            results.append({
                "tx1_mode": i,
                "tx2_mode": j,
                "v_rx_volts": v_rx
            })

            print(f"TX1={i}, TX2={j} → Vrx={v_rx:.6f} V")

    # Save CSV
    with open(OUTPUT_CSV, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["tx1_mode", "tx2_mode", "v_rx_volts"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults saved to {OUTPUT_CSV}")
    return results

def plot_results(results):
    """
    Bar plot of RX voltage for each TX mode combination.
    """
    labels = [f"{r['tx1_mode']},{r['tx2_mode']}" for r in results]
    values = [r["v_rx_volts"] for r in results]

    plt.figure(figsize=(10, 5))
    plt.plot(labels, values, marker='o', linestyle='-')  # line with points
    plt.xlabel("TX Mode Combination (TX1,TX2)")
    plt.ylabel("RX Voltage (Volts)")
    plt.title("RX Voltage for TX Mode Combinations")
    plt.grid(True)
    plt.xticks(rotation=45)  # rotate labels for readability
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    results = run_feedback_phase_sweep()
    plot_results(results)