import argparse
import json
import os
import sys
from tag import Tag

CONFIG_PATH = "config.json"


def load_config():
    """Loads config file, gaining information it needs to run

    Returns:
        tags,actions,default: List of information thats stored in JSON file
    """

    DEFAULT_STATS = {"exciter_power": 500.0, "gain": 0.0, "resistive_load": 50}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            raw_data = json.load(f)

        raw_objects = raw_data.get("Objects", {})
        raw_actions = raw_data.get("Actions", [])
        default = raw_data.get("Default")
        tags = {uid: Tag.from_dict(uid, val) for uid, val in raw_objects.items()}
        actions = [action for action in raw_actions]
        return tags, actions, default
    else:
        return {}, [], DEFAULT_STATS


def save_config(objects, actions, default):
    """offloads changes back to JSON file

    Args:
        tags (dict): Dictionary of the tags that are in the system
        actions (list): List of actions that simulation will peform
    """
    with open(CONFIG_PATH, "w") as f:
        json.dump(
            {
                "Default": {
                    "exciter_power": default["exciter_power"],  # (mW)
                    "gain": 0,  # (dBi) Isotropic by default
                    "resistive_load": default["resistive_load"],  # (ohms)
                },
                "Objects": {uid: objects.to_dict() for uid, objects in objects.items()},
                "Actions": [action for action in actions],
            },
            f,
        )


def parse_obj(vals, tags):
    """Ensures the tag argument has the correct values
    Args:
        vals (List): tag UID, and its coordinats

    Returns:
        _type_: _description_
    """
    uid = vals[0]
    try:
        coords = [float(v) for v in vals[1:]]
    except ValueError as e:
        print("error: coordinates given are not numerical values")
        sys.exit(1)
    return uid, coords[0], coords[1], coords[2]


def parse_default(vals, default):
    try:
        val = float(vals[1])
        default[vals[0]] = val
    except ValueError as e:
        print("error: invalid values for default")
        sys.exit(1)
    return default


def parse_args():
    """Parses arguments, can be in any order

    Returns:
        ArgumentParser: Argument parser which holds values of which arguments where given
    """
    parser = argparse.ArgumentParser(description="Tag-to-Tag Network Simulator")
    parser.add_argument(
        "--tag",
        nargs=4,
        metavar=("UID", "X", "Y", "Z"),
        required=False,
        help="place a tag with its Unique ID at coordinates X,Y,Z",
    ),
    parser.add_argument(
        "--exciter",
        nargs=4,
        metavar=("UID", "X", "Y", "Z"),
        required=False,
        help="place an exciter with its Unique ID at coordinates X,Y,Z",
    ),
    parser.add_argument(
        "--remove", type=str, required=False, help="Remove a specific tag based on UID"
    )
    parser.add_argument("--print", type=str, help="Arguments; actions,objects")

    parser.add_argument(
        "--action",
        nargs=3,
        metavar=("tx", "rx", "protocol"),
        help="An action that will be simulated",
    )
    parser.add_argument(
        "--default", nargs=2, metavar=("name", "value"), help="changes a default value"
    )
    parser.add_argument("--load", type=str, help="text file to be loaded in")

    return parser.parse_args()


# need to update this to close for incorrect formated files
def load(filepath):
    """Loads configs from a text file, easier for users to make then the json config

    Args:
        filepath (string): text file to load in

    Returns:
        object,actions,default: information about the simulation configurations
    """
    default = {}
    actions = []
    objects = {}
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            mode = "default"
            lines = f.readlines()
            for line in lines:
                line = line.strip().lower()
                if line == "exciter:":
                    mode = "exciter"
                    continue
                elif line == "action:":
                    mode = "action"
                    continue
                elif line == "tag:":
                    mode = "tag"
                    continue
                elif ":" in line:  # for default values
                    mode = "default"
                    info = line.split(":")
                    default[info[0]] = float(info[1])
                    continue

                # if mode wasnt changed, then it will expect a action/tag/exciter
                if mode == "exciter":
                    info = line.split()
                    tag = Tag(info[0], "exciter", info[1], info[2], info[3])
                    objects[info[0]] = tag
                elif mode == "tag":
                    info = line.split()
                    tag = Tag(info[0], "tag", info[1], info[2], info[3])
                    objects[info[0]] = tag
                elif mode == "action":
                    info = line.split()
                    actions.append(info[:3])
        return objects, actions, default


def main():

    objects, actions, default = load_config()
    args = parse_args()

    if args.load is not None:  # load in a file
        objects, actions, default = load(args.load)

    if (
        args.tag is not None or args.exciter is not None
    ):  # Creates or move a tag/exciter
        obj_args = None
        model = None
        if args.tag is not None:
            model = "tag"
            obj_args = args.tag
        else:
            model = "exciter"
            obj_args = args.exciter

        uid, x, y, z = parse_obj(obj_args, objects)

        tag = Tag(uid, model, x, y, z)
        tag.resistance = default["resistive_load"]
        if args.exciter:
            tag.gain = default["gain"]
            tag.power = default["exciter_power"]
            tag.model = "exciter"
        if uid in objects:
            print(model + ":", uid, "Moved to coordinates", x, y, z)
        else:
            print(model + ":", uid, "Added at coordinate", x, y, z)
        objects[uid] = tag

    if args.default is not None:  # updates default value
        default = parse_default(args.default, default)
        print("updated")

    if args.remove:  # removes an object (Tag or exciter)
        if args.remove in objects:
            del objects[args.remove]
        else:
            print("unkown id")

    if args.print:  ## prints out information
        if args.print == "objects":
            for key, value in objects.items():
                print(f"{key}: {value.to_dict()}")
        elif args.print == "actions":
            for index, value in enumerate(actions, start=1):
                print(index, value)
        elif args.print == "default":
            units = ["mW", "dBi", "Ohm"]  # for display purpose
            for i, (key, value) in enumerate(default.items()):
                print(f"{key}: {value} {units[i]}")

    if args.action:  # adds an action
        action = args.action
        if action[0] not in objects:
            print("error, unkown tag:", action[0])
        elif action[1] not in objects:
            print("error, unkown tag:", action[1])
        actions.append(args.action)
    save_config(objects, actions, default)


if __name__ == "__main__":
    main()
