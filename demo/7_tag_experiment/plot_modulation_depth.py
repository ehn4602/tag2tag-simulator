import numpy as np
import matplotlib.pyplot as plt
import os
import json
from collections import defaultdict
from scipy.stats import gaussian_kde


DISTANCE_OFFSET = 1.0  # meters
DISTANCE_INCREMENT = 1 / 100  # meters


def parse_log_one():
    one_helper_dir = "one_helper/logs"
    logs = [os.path.join(one_helper_dir, f) for f in os.listdir(
        one_helper_dir) if os.path.isfile(os.path.join(one_helper_dir, f))]
    logs.sort(key=os.path.getmtime)

    configurations = []

    i = 0
    for log in logs[-5:]:
        configurations.append(defaultdict(list))
        index = None
        helper = None
        with open(log, 'r') as f:
            for line in f:
                if not line:
                    continue
                log_line = json.loads(line)
                if 'Hx' in log_line["tag"]:
                    helper = log_line["tag"]
                    index = int(log_line["mode"]["chip_index"])
                if helper is not None and 'voltage' in log_line:
                    configurations[i][(helper, index)].append(
                        log_line["voltage"])
                    index = None
            i += 1

    modulation_depth_dict = defaultdict(int)
    optimal_configs = []
    print(configurations)

    for v in configurations:

        max_modulation_depth = 0
        optimal_config = None

        for k1, v1 in v.items():
            modulation_depth = abs(v1[0] - v1[1])
            modulation_depth_dict[k1] = modulation_depth
            if modulation_depth > max_modulation_depth:
                max_modulation_depth = modulation_depth
                optimal_config = [k1, v1]

        optimal_configs.append(optimal_config)

    sorted_dict = {}
    for key in sorted(modulation_depth_dict, key=modulation_depth_dict.get):
        sorted_dict[key] = modulation_depth_dict[key]

    return modulation_depth_dict, optimal_configs


def parse_log_variable(log_file: str, num_helpers: int):
    logs = [os.path.join(log_file, f) for f in os.listdir(
        log_file) if os.path.isfile(os.path.join(log_file, f))]
    logs.sort(key=os.path.getmtime)

    configurations = []

    i = 0
    for log in logs:
        # print("New Log")
        configurations.append(defaultdict(list))
        # Helper and corresponding index list
        helpers = []
        indices = []
        with open(log, 'r') as f:
            for line in f:
                # Empty Line
                if not line:
                    continue
                log_line = json.loads(line)
                # Checks if the log line contains information about a helper tag
                if 'Hx' in log_line["tag"]:
                    # Checks if helper is already in the helper list
                    if log_line["tag"] in helpers:
                        # Change the index in the index table
                        # print(helpers)
                        # print(indices)
                        # print(int(log_line["tag"][2:]))
                        indices[helpers.index(log_line["tag"])] = int(
                            log_line["mode"]["chip_index"])

                    else:
                        # Add helper tag and chip index to their respective lists
                        helpers.append(log_line["tag"])
                        indices.append(int(log_line["mode"]["chip_index"]))
                if len(helpers) == num_helpers and 'voltage' in log_line:
                    configurations[i][(tuple(helpers), tuple(indices))].append(
                        log_line["voltage"])
            i += 1

    # for i in configurations:
    #     print(i)

    """
    Configurations 
        Every key represents a different log file
        Every log file has a different subset of tags
        Every subset of tags will go through every possible phase for each tag

        Structure
        configurations = [{Key: (Subset of tag names tuple, chip indices of tags tuple), Value: A list of two integer values representing voltages}]

    """

    modulation_depth_dict = defaultdict(int)
    optimal_configs = []

    for v in configurations:

        max_modulation_depth = 0
        optimal_config = None

        for k1, v1 in v.items():
            modulation_depth = abs(v1[0] - v1[1])
            modulation_depth_dict[k1] = modulation_depth
            if modulation_depth > max_modulation_depth:
                max_modulation_depth = modulation_depth
                optimal_config = [k1, modulation_depth]

        optimal_configs.append(optimal_config)

    # print(optimal_configs)

    sorted_dict = {}
    for key in sorted(modulation_depth_dict, key=modulation_depth_dict.get):
        sorted_dict[key] = modulation_depth_dict[key]

    # print(list(sorted_dict.values())[-5:])

    return sorted_dict, optimal_configs


def parse_log_none():
    log_file = 'zero_helpers/logs'

    logs = [os.path.join(log_file, f) for f in os.listdir(
            log_file) if os.path.isfile(os.path.join(log_file, f))]
    logs.sort(key=os.path.getmtime)
    voltages = []
    for log in logs:
        with open(log, 'r') as f:
            for line in f:
                if not line:
                    continue

                log_line = json.loads(line)
                if "voltage" in line:
                    voltages.append(float(log_line["voltage"]))

    print(voltages)

    return [abs(voltages[1] - voltages[0])]


def plot():
    one_dict, one_optimal_set = parse_log_variable('one_helper/logs', 1)
    two_dict, two_optimal_set = parse_log_variable('two_helpers/logs', 2)
    three_dict, three_optimal_set = parse_log_variable('three_helpers/logs', 3)
    four_dict, four_optimal_set = parse_log_variable('four_helpers/logs', 4)
    five_dict, five_optimal_set = parse_log_variable('five_helpers/logs', 5)

    zero_values = parse_log_none()

    # print(len(five_dict.values()))

    y_groups = [
        zero_values,
        one_dict.values(),
        two_dict.values(),
        three_dict.values(),
        four_dict.values(),
        five_dict.values()
    ]

    for i, y in enumerate(y_groups, start=0):
        plt.scatter([i]*len(y), y, color='grey')

    plt.xlabel("Number of Helpers")
    plt.ylabel("Modulation Depth(mv)")
    plt.title("Vertical Scatter Plot")
    plt.show()


if __name__ == "__main__":
    plot()
