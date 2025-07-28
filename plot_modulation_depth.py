import numpy as np
import matplotlib.pyplot as plt


DISTANCE_OFFSET = 1.0  # meters
DISTANCE_INCREMENT = 1 / 100  # meters


def plot_modulation_depth():
    data = np.genfromtxt(
        "processed.csv", delimiter=",", dtype=None, names=True, encoding="utf-8"
    )

    tags = [
        (int(tag.strip('"')) * DISTANCE_INCREMENT) + DISTANCE_OFFSET
        for tag in data["tag"]
    ]
    modulation_depths = data["modulation_depth"]

    plt.figure()
    plt.plot(tags, modulation_depths)

    plt.title("Modulation Depth by Distance")
    plt.xlabel("Distance (meters)")
    plt.ylabel("Modulation Depth")
    plt.grid(True)
    plt.xlim((2,4))

    plt.show()


def print_tags():
    """
    Prints the tags in the format expected by the simulator.
    """
    for i in range(0, 10 / DISTANCE_INCREMENT):
        distance = DISTANCE_OFFSET + i * DISTANCE_INCREMENT
        print(f"tag {i:04d} {distance} 0 0")


if __name__ == "__main__":
    # print_tags()
    plot_modulation_depth()
