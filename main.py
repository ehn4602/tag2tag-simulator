import argparse
import bisect
import heapq
import json
import logging
import os
import queue
import sys
from logging.handlers import QueueHandler, QueueListener
from pathlib import Path

from tags.tag import Tag, TagMachine
from state_machine import *

CONFIG_PATH = "./config/config.json"
STATE_PATH = "./config/state_machines.json"

DEFAULT_STATS = {
    "exciter_power": 500.0,
    "gain": 0.0,
    "resistive_load": 50,
    "input_machine_id": "UNKNOWN",
    "proccessing_machine_id": "UNKOWN",
    "output_machine_id": "UNKNOWN",
}


def load_json(file_input, serializer, machines=None):
    """Loads config file, gaining information it needs to run

    Returns:
        tags,events,default: List of information thats stored in JSON file
    """

    if os.path.exists(file_input):
        with open(file_input, "r") as f:
            try:
                raw_data = json.load(f)
            except json.JSONDecodeError:
                if file_input == CONFIG_PATH:
                    return None, {}, [], DEFAULT_STATS
                elif file_input == STATE_PATH:
                    return {}, None, None, None
                else:
                    print("error: file doesn't exist")
                    sys.exit(1)
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
                    "input_machine_id": default["input_machine_id"],
                    "proccessing_machine_id": default["proccessing_machine_id"],
                    "output_machine_id": default["output_machine_id"],
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
    except ValueError:
        print("error: coordinates given are not numerical values")
        sys.exit(1)
    return id, coords[0], coords[1], coords[2]


def parse_default(vals, default, machines):
    if vals[0] in ["exciter_power", "resistive_load", "gain"]:
        try:
            val = float(vals[1])
            default[vals[0]] = val
        except ValueError:
            print("error: invalid values for default")
            sys.exit(1)
        return default
    elif vals[0] in ["input", "proccessing", "output"] and machines is not None:
        val = ""
        val += vals[0]
        val += "_machine_id"
        if vals[1] in machines:
            default[val] = vals[1]
            return default
        else:
            print("error: state machine {" + vals[1] + "} does not exist")
            sys.exit(1)
    print("error: invalid default argument")
    sys.exit(1)


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


def load(filepath, serializer):
    """Loads arguments via a text file. Format is the same as arguments
    Args:
        filepath (string): text file to load in

    Returns:
        objects,events,default: information about the simulation configuration
    """

    default = DEFAULT_STATS
    events = []
    objects = {}
    machines = {}
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
                    tag = TagMachine(info[1], info[2:5])
                    tag.input_machine = default.get("input_machine_id")
                    tag.processing_machine = default.get("proccessing_machine_id")
                    tag.output_machine = default.get("output_machine_id")
                    objects[info[1]] = tag
                elif info[0] == "exciter":
                    tag = TagMachine(info[1], info[2:5])
                    objects[info[1]] = tag
                elif info[0] == "default":
                    default = parse_default(info[1:3], default, machines)
                    # default[info[1]] = float(info[2])
                elif info[0] == "event":
                    event = info[1:]
                    times = [e[0] for e in events]
                    position = bisect.bisect_left(times, info[1])
                    events.insert(position, event)
                elif info[0] == "load":
                    if os.path.exists(info[1]):
                        with open(info[1], "r") as f:
                            try:
                                raw_data = json.load(f)
                            except json.JSONDecodeError:
                                print("Skipping! invalid filepath:", info[1])
                        if raw_data.get("Format") in [
                            "input_machine",
                            "proccessing_machine",
                            "output_machine",
                        ]:
                            machine = load_machine(raw_data, serializer)
                            machines[machine.id] = machine
                        else:
                            print("Skipping! invalid format:", info[1])

            return machines, objects, events, default


def init_logger(
    level, filename="tagsim.log", stdout=False
) -> tuple[logging.Logger, QueueListener]:
    """
    Initializes a logger that can then be used throughout the program.

    Arguments:
    level -- The logging level to log at
    filename -- Name of the file where the log is to be stored, tagsim.log in
                PWD by default.
    stdout -- Whether or not to print Log to stdout. False by default.

    Returns: The handle to the logger
    """
    log_queue = queue.Queue()
    qh = QueueHandler(log_queue)

    logger = logging.getLogger(__name__)
    logging.basicConfig(
        handlers=[qh],
        format=f"%(asctime)s::%(levelname)s::{Path(__file__).name}: %(msg)s",
        level=level,
    )

    block_handlers = []

    fhandle = logging.FileHandler(filename)
    block_handlers.append(fhandle)

    if stdout:
        shandle = logging.StreamHandler()
        block_handlers.append(shandle)

    ql = QueueListener(log_queue, *block_handlers)
    ql.start()
    return logger, ql


def init_logger(
    level, filename="tagsim.log", stdout=False
) -> tuple[logging.Logger, QueueListener]:
    """
    Initializes a logger that can then be used throughout the program.

    Arguments:
    level -- The logging level to log at
    filename -- Name of the file where the log is to be stored, tagsim.log in
                PWD by default.
    stdout -- Whether or not to print Log to stdout. False by default.

    Returns: The handle to the logger
    """
    log_queue = queue.Queue()
    qh = QueueHandler(log_queue)

    logger = logging.getLogger(__name__)
    logging.basicConfig(
        handlers=[qh],
        format=f"%(asctime)s::%(levelname)s::{Path(__file__).name}: %(msg)s",
        level=level,
    )

    block_handlers = []

    fhandle = logging.FileHandler(filename)
    block_handlers.append(fhandle)

    if stdout:
        shandle = logging.StreamHandler()
        block_handlers.append(shandle)

    ql = QueueListener(log_queue, *block_handlers)
    ql.start()
    return logger, ql


def main():

    serializer = StateSerializer()
    machines = {}
    machines, _, _, _ = load_json(STATE_PATH, serializer)
    _, objects, events, default = load_json(CONFIG_PATH, serializer, machines=machines)

    # if machine is not None:
    #     machines[machine.id] = machine
    args = parse_args()

    # TODO Change this to take in arguments from the command line
    logger, q_listener = init_logger(logging.INFO)

    if args.load is not None:  # load in a file
        file_type = args.load.split(".")[-1]
        if file_type == "txt":
            if args.add:  # appends loaded arguments instead of overwrite
                add_machines, add_objects, add_events, add_default = load(
                    args.load, serializer
                )
                objects.update(add_objects)
                default.update(add_default)
                machines.update(add_machines)
                events = list(heapq.merge(events, add_events, key=lambda x: x[0]))
            else:  # overwrites previouse saved data
                machines, objects, events, default = load(args.load, serializer)
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
        tag = TagMachine(id, coordinates)
        if args.tag:
            tag.input_machine = default.get("input_machine_id")
            tag.processing_machine = default.get("proccessing_machine_id")
            tag.output_machine = default.get("output_machine_id")
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
        default = parse_default(args.default, default, machines)
        print("updated")

    if args.remove:  # removes an object (Tag or exciter)
        if args.remove in objects:
            del objects[args.remove]
        else:
            print("unkown id")

    if args.print:  ## prints out information
        lower_args = args.print.lower()
        match lower_args:
            case "objects":
                for key, value in objects.items():
                    print(f"{key}: {value.to_dict()}")
            case "events":
                for index, value in enumerate(events, start=1):
                    print(index, value)
            case "default":
                units = ["mW", "dBi", "Ohm"]  # for display purpose
                for i, (key, value) in enumerate(default.items()):
                    if i < 3:
                        print(f"{key}: {value} {units[i]}")
                    else:
                        print(f"{key}: {value}")
            case "states":
                for key, value in serializer.mappings.items():
                    print(f"{value}: {key.to_dict(serializer)}")
            case "machines":
                for key, value in machines.items():
                    print(f"{key}: {value.to_dict(serializer,"placeholder")}")

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
    q_listener.stop()


if __name__ == "__main__":
    main()
