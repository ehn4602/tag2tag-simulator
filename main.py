import argparse
import json
import os
import sys
import bisect
import heapq
from tag import Tag
from state_machine import *

CONFIG_PATH = "./config/config.json"
STATE_PATH = "./config/state_machines.json"


# TODO figure out how to format state machine as JSON
def load_json(file_input, serializer, machines=None):
    """Loads config file, gaining information it needs to run

    Returns:
        tags,events,default: List of information thats stored in JSON file
    """

    DEFAULT_STATS = {"exciter_power": 500.0, "gain": 0.0, "resistive_load": 50}
    if os.path.exists(file_input):
        with open(file_input, "r") as f:
            raw_data = json.load(f)
        format = raw_data.get("Format")
        if format == "config":
            raw_objects = raw_data.get("Objects", {})
            raw_events = raw_data.get("events", [])

            default = raw_data.get("Default")
            tags = {
                id: TagMachine.from_dict(id, val, machines)
                for id, val in raw_objects.items()
            }
            events = [event for event in raw_events]
            return None, tags, events, default
        elif format == "state_machine":
            raw_states = raw_data.get("states", [])
            raw_machines = raw_data.get("state_machines", [])
            for state in raw_states:
                State.from_dict(state.get("id"), state, serializer)
            machines = {
                mach["id"]: StateMachine.from_dict(serializer, mach)
                for mach in raw_machines
            }
            return machines, None, None, None
        else:
            machine = load_machine(raw_data, serializer)
            if machine is None:
                print("error: invalid JSON format")
                sys.exit(1)
            else:
                return machine, None, None, None
    elif file_input == CONFIG_PATH:
        return None, {}, [], DEFAULT_STATS
    elif file_input == STATE_PATH:
        return {}, None, None, None
    else:
        print("error: file doesn't exist")
        sys.exit(1)


def save_config(machines, objects, events, default, serializer):
    """offloads changes back to JSON file

    Args:
        tags (dict): Dictionary of the tags that are in the system
        events (list): List of events that simulation will peform
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
                "Objects": {id: obj.to_dict() for id, obj in objects.items()},
                "events": events,
            },
            f,
            indent=4,
        )
    with open("./config/state_machines.json", "w") as f:
        json.dump(
            {
                "Format": "state_machine",
                "state_machines": [
                    mach.to_dict(serializer, "placeholder")
                    for mach in machines.values()
                ],
                "states": serializer.to_dict(),
            },
            f,
            indent=4,
        )


def parse_obj(vals, tags):
    """Ensures the tag argument has the correct values
    Args:
        vals (List): tag ID, and its coordinats

    Returns:
        _type_: _description_
    """
    id = vals[0]
    try:
        coords = [float(v) for v in vals[1:]]
    except ValueError as e:
        print("error: coordinates given are not numerical values")
        sys.exit(1)
    return id, coords[0], coords[1], coords[2]


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
        metavar=("ID", "X", "Y", "Z"),
        required=False,
        help="place a tag with its Unique ID at coordinates X,Y,Z",
    ),
    parser.add_argument(
        "--exciter",
        nargs=4,
        metavar=("ID", "X", "Y", "Z"),
        required=False,
        help="place an exciter with its Unique ID at coordinates X,Y,Z",
    ),
    parser.add_argument(
        "--remove", type=str, required=False, help="Remove a specific tag based on ID"
    )
    parser.add_argument("--print", type=str, help="Arguments; events,objects")

    parser.add_argument(
        "--event",
        nargs=4,
        metavar=("HH:MM:SS", "tx", "rx", "protocol"),
        help="An event that will be simulated",
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


def load_machine(data, serializer):

    if (
        data.get("Format") == "input_machine"
        or data.get("Format") == "proccessing_machine"
        or data.get("Format") == "output_machine"
    ):
        raw_states = data.get("states", [])
        for state in raw_states:
            State.from_dict(state.get("id"), state, serializer)
        init_state = serializer._map_id_to_state(data.get("init_state"))
        machine = StateMachine(init_state, data.get("id"))
        print(data.get("Format"), "successfully loaded")
        return machine
    else:
        return None


def load(filepath):
    """Loads arguments via a text file. Format is the same as arguments
    Args:
        filepath (string): text file to load in

    Returns:
        objects,events,default: information about the simulation configuration
    """

    default = {}
    events = []
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
                elif info[0] == "event":
                    event = info[1:]
                    times = [e[0] for e in events]
                    position = bisect.bisect_left(times, info[1])
                    events.insert(position, event)
            return objects, events, default


def main():

    serializer = StateSerializer()
    machines = {}
    machines, _, _, _ = load_json(STATE_PATH, serializer)
    _, objects, events, default = load_json(CONFIG_PATH, serializer, machines=machines)

    # if machine is not None:
    #     machines[machine.id] = machine
    args = parse_args()

    if args.load is not None:  # load in a file
        file_type = args.load.split(".")[-1]
        if file_type == "txt":
            if args.add:  # appends loaded arguments instead of overwrite
                add_objects, add_events, add_default = load(args.load)
                objects.update(add_objects)
                default.update(add_default)
                events = list(heapq.merge(events, add_events, key=lambda x: x[0]))
            else:  # overwrites previouse saved data
                objects, events, default = load(args.load)
        elif file_type == "json":
            machine, temp_objects, temp_events, temp_default = load_json(
                args.load, serializer, machines=machines
            )
            if (
                temp_objects is not None
                or temp_events is not None
                or temp_default is not None
            ):
                objects = temp_objects
                events = temp_events
                default = temp_default
            if machine is not None:
                machines[machine.id] = machine
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

        id, x, y, z = parse_obj(obj_args, objects)

        # tag = Tag(uid, model, x, y, z)
        coordinates = [x, y, z]
        tag = StateMachine(id, coordinates)

        # Removed for now
        # tag.resistance = default["resistive_load"]
        # if args.exciter:
        #     tag.gain = default["gain"]
        #     tag.power = default["exciter_power"]
        #     tag.model = "exciter"
        if id in objects:
            print(model + ":", id, "Moved to coordinates", x, y, z)
        else:
            print(model + ":", id, "Added at coordinate", x, y, z)
        objects[id] = tag

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
        elif args.print == "events":
            for index, value in enumerate(events, start=1):
                print(index, value)
        elif args.print == "default":
            units = ["mW", "dBi", "Ohm"]  # for display purpose
            for i, (key, value) in enumerate(default.items()):
                print(f"{key}: {value} {units[i]}")

    # Events will be reconfigure later to work along side events.json
    if args.event:  # adds an event
        event = args.event
        if event[1] not in objects:
            print("error, unkown tag:", event[1])
        elif event[2] not in objects:
            print("error, unkown tag:", event[2])
        else:
            times = [a[0] for a in events]
            position = bisect.bisect_left(times, event[0])
            events.insert(position, event)
            events.append(args.event)
    save_config(machines, objects, events, default, serializer)


if __name__ == "__main__":
    main()
