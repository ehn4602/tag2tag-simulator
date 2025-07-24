import numpy as np
import matplotlib.pyplot as plt


def plot_modulation_depth():
    data = np.genfromtxt(
        "processed.csv", delimiter=",", dtype=None, names=True, encoding="utf-8"
    )

    tags = data["tag"]
    modulation_depths = data["modulation_depth"]

    plt.figure()
    plt.plot(tags, modulation_depths)

    plt.title("Modulation Depth by Tag")
    plt.xlabel("Tag")
    plt.ylabel("Modulation Depth")
    plt.grid(True)

    plt.show()


if __name__ == "__main__":
    plot_modulation_depth()
