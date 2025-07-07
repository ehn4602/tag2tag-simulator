import argparse
import json
import os
import sys
import bisect
import heapq
from tag import Tag

CONFIG_PATH = "config.json"


# TODO figure out how to format state machine as JSON 
def load_json(file_input):
    """Loads config file, gaining information it needs to run

    Returns:
        tags,actions,default: List of information thats stored in JSON file
    """

    DEFAULT_STATS = {"exciter_power": 500.0, "gain": 0.0, "resistive_load": 50}
    if os.path.exists(file_input):
        with open(file_input, "r") as f:
            raw_data = json.load(f)

        if raw_data.get("Format") == "config":
            raw_objects = raw_data.get("Objects", {})
            raw_actions = raw_data.get("Actions", [])

            default = raw_data.get("Default")
            tags = {uid: Tag.from_dict(uid, val) for uid, val in raw_objects.items()}
            actions = [action for action in raw_actions]
            return None,tags, actions, default
        elif raw_data.get("Format") == "input_machine":   
            print("input machine loaded")  
            return None, None, None, None                   # Placeholder 
        elif raw_data.get("Format") == "processing_machine": 
            print("processing machine loaded")  
            return None, None, None, None                   # Placeholder
        elif raw_data.get("Format") == "output_machine":
            print("output machine loaded")  
            return None, None, None, None                  # Placeholder
        else:
            print("error: invalid JSON format")
            sys.exit(1)
    elif file_input == CONFIG_PATH:
         return None,{}, [], DEFAULT_STATS
    else:
        print("error: file doesn't exist")
        sys.exit(1)

def save_config(objects, actions, default):
    """offloads changes back to JSON file

    Args:
        tags (dict): Dictionary of the tags that are in the system
        actions (list): List of actions that simulation will peform
    """
    with open(CONFIG_PATH, "w") as f:
        json.dump(
            {
                "Format": "config",
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
        nargs=4,
        metavar=("HH:MM:SS", "tx", "rx", "protocol"),
        help="An action that will be simulated",
    )
    parser.add_argument(
        "--default", nargs=2, metavar=("name", "value"), help="changes a default value"
    )
    parser.add_argument("--load", type=str, help="text file to be loaded in")
    parser.add_argument(
        "--add",
        action="store_true",
        help="makes loading add onto the existing data rather than overwriting",
    )

    return parser.parse_args()


def load(filepath):
    """Loads arguments via a text file. Format is the same as arguments
    Args:
        filepath (string): text file to load in

    Returns:
        objects,actions,default: information about the simulation configuration
    """

    default = {}
    actions = []
    objects = {}
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            lines = f.readlines()
            for line in lines:
                line = line.split("#", 1)[
                    0
                ].strip()  # remove comments from loading files. Comments start with #
                if not line:  # line is just a comment
                    continue
                info = line.lower().split(" ")
                if info[0] == "tag":
                    tag = Tag(info[1], info[0], info[2], info[3], info[4])
                    objects[info[1]] = tag
                elif info[0] == "exciter":
                    tag = Tag(info[1], info[0], info[2], info[3], info[4])
                    objects[info[1]] = tag
                elif info[0] == "default":
                    default[info[1]] = float(info[2])
                elif info[0] == "action":
                    action = info[1:]
                    times = [a[0] for a in actions]
                    position = bisect.bisect_left(times, info[1])
                    actions.insert(position, action)
            return objects, actions, default


def main():

    machine, objects, actions, default = load_json(CONFIG_PATH)
    args = parse_args()

    if args.load is not None:  # load in a file
        file_type = args.load.split(".")[1]
        if file_type=="txt":
            if args.add:  # appends loaded arguments instead of overwrite
                add_objects, add_actions, add_default = load(args.load)
                objects.update(add_objects)
                default.update(add_default)
                actions = list(heapq.merge(actions, add_actions, key=lambda x: x[0]))
            else:  # overwrites previouse saved data
                objects, actions, default = load(args.load)
        elif file_type == "json":
            machine, temp_objects,temp_actions,temp_default = load_json(args.load)
            if(temp_objects is not None or temp_actions is not None or temp_default is not None):
                objects = temp_objects
                actions = temp_actions
                default = temp_default
        else:
            print("error: file type not supported")
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
        if action[1] not in objects:
            print("error, unkown tag:", action[1])
        elif action[2] not in objects:
            print("error, unkown tag:", action[2])
        else:
            times = [a[0] for a in actions]
            position = bisect.bisect_left(times, action[0])
            actions.insert(position, action)
            actions.append(args.action)
    save_config(objects, actions, default)


if __name__ == "__main__":
    main()
