import argparse
import bisect
import heapq
import json
import logging
import os
import queue
import sys
import heapq
from logging.handlers import QueueHandler, QueueListener
from pathlib import Path
from typing import Optional

from tags.tag import *
from tags.state_machine import *
from event.base_event import *

CONFIG_PATH = "./config/config.json"
STATE_PATH = "./config/states.json"
EVENT_PATH = "./config/events.json"

DEFAULT_STATS = {
    "exciter_power": 500.0,
    "gain": 0.0,
    "resistive_load": 50,
    "input_machine_id": "UNKNOWN",
    "proccessing_machine_id": "UNKOWN",
    "output_machine_id": "UNKNOWN",
}


def load_json(
    file_input: str,
    serializer: StateSerializer,
    timer: Optional[TimerScheduler] = None,
    logger: Optional[logging.Logger] = None,
    environment: Optional[Environment] = None,
    default: Optional[dict] = None,
):
    """Loads config file, gaining information it needs to run

    Returns:
        exciter,tags,events,default: List of information thats stored in JSON file
    """

    default_exciter = Exciter(environment, "default", (0, 0, 0))
    if os.path.exists(file_input):
        with open(file_input, "r") as f:
            try:
                raw_data = json.load(f)
            except json.JSONDecodeError:
                if file_input == CONFIG_PATH:
                    return default_exciter, {}, None, DEFAULT_STATS
                elif file_input == EVENT_PATH:
                    return None, None, [], None
                else:
                    print("error: file doesn't exist")
                    sys.exit(1)
        format = raw_data.get("Format")
        if format == "config":
            raw_objects = raw_data.get("Objects", {})
            # raw_events = raw_data.get("events", [])

            default = raw_data.get("Default")
            if raw_data.get("Exciter") != "UNDEFINED":
                exciter = Exciter.from_dict(environment, raw_data.get("Exciter"))
            else:
                exciter = default_exciter
            tags = {
                id: Tag.from_dict(environment, logger, timer, id, val, serializer)
                for id, val in raw_objects.items()
            }
            # events = [event for event in raw_events]
            return exciter, tags, None, default
        elif format == "state_machine":
            state_output = load_states(raw_data, serializer, default)
            if state_output is not None:
                return None, None, None, state_output
        elif format == "events":
            events = [EventArgs.from_dict(e) for e in raw_data.get("Events")]
            return None, None, events, None
        else:
            print("error: invalid JSON format")
            sys.exit(1)
    elif file_input == CONFIG_PATH:
        return default_exciter, {}, [], DEFAULT_STATS
    elif file_input == STATE_PATH:
        return {}, None, None, None
    else:
        print("error: file doesn't exist")
        sys.exit(1)
    return None, None, None, None


def save_config(
    exciter: Exciter,
    objects: dict,
    events: list,
    default: dict,
    serializer: StateSerializer,
):
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
                "Exciter": (
                    Exciter.to_dict(exciter) if exciter is not None else "UNDEFINED"
                ),
                "Objects": {id: obj.to_dict() for id, obj in objects.items()},
            },
            f,
            indent=4,
        )
    with open(STATE_PATH, "w") as f:
        json.dump(
            {
                "Format": "state_machine",
                "states": serializer.to_dict(),
            },
            f,
            indent=4,
        )
    with open(EVENT_PATH, "w") as f:
        json.dump(
            {"Format": "events", "Events": [e.to_dict() for e in events]},
            f,
            indent=4,
        )


def parse_obj(vals: list):
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


def parse_default(vals, default: dict, serializer: StateSerializer):
    """parses argumnet values to fill out default value correctly

    Args:
        vals (List): List of vals given via argument
        default (Dict): Dictionary representing default information
        serializer (StateSerializer): serializer with information about the known states in the system

    Returns:
        default: updated dictionary
    """
    if vals[0] in ["exciter_power", "resistive_load", "gain"]:
        try:
            val = float(vals[1])
            default[vals[0]] = val
        except ValueError:
            print("error: invalid values for default")
            sys.exit(1)
        return default
    elif vals[0] in ["input", "proccessing", "output"]:
        val = ""
        val += vals[0]
        val += "_machine_id"
        if vals[1] in serializer.get_state_map().keys():
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
        nargs=3,
        metavar=("X", "Y", "Z"),
        required=False,
        help="moves the exciter to coordinates X,Y,Z",
    ),
    parser.add_argument(
        "--remove", type=str, required=False, help="Remove a specific tag based on ID"
    )
    parser.add_argument("--print", type=str, help="Arguments; events,objects")

    parser.add_argument(
        "--event",
        nargs=3,
        metavar=("time", "tag", "event_type"),
        help="An event that will be simulated",
    )
    parser.add_argument("--event_transmission", nargs=1, help="")
    parser.add_argument("--event_mode", nargs=1, help="")

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


def load_states(data: dict, serializer: StateSerializer, default: dict):
    """loads states from state_machine or states config file

    Args:
        data (dict): JSON dict file
        serializer (StateSerializer): Serializer with information about states within the system
        default (dict): dictionary with default information

    Returns:
        default: updated default, only updates if state_machine loaded with type value on it.
    """

    format_type = "State machine"
    raw_states = data.get("states", [])
    for state in raw_states:
        State.from_dict(state, serializer)
    if "type" in data:
        format_type = "State machine"
        if data.get("type") == "input_machine":
            default["input_machine_id"] = data.get("init_state")
            format_type = "Input machine"
        elif data.get("type") == "proccessing_machine":
            default["proccessing_machine_id"] = data.get("init_state")
            format_type = "Proccessing machine"
        elif data.get("type") == "output_machine":
            default["output_machine_id"] = data.get("init_state")
            format_type = "Proccessing machine"
        print(format_type, "successfully loaded")
        return default
    else:
        return None


def load_txt(
    filepath: str,
    environment: Environment,
    serializer: StateSerializer,
    logger: logging,
):
    """Loads arguments via a text file. Format is the same as arguments
    Args:
        filepath (string): text file to load in

    Returns:
        objects,events,default: information about the simulation configuration
    """

    timer = None  # Placeholder, remove later

    default = DEFAULT_STATS
    events = []
    objects = {}
    exciter = None
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            lines = f.readlines()
            for line in lines:
                line = line.split("#", 1)[
                    0
                ].strip()  # remove comments from loading files. Comments start with #
                if not line:  # line is just a comment
                    continue

                info = line.replace("-", "").split(" ")
                info[0] = info[0].lower()
                if info[0] == "tag":

                    init_states = []
                    init_states.append(
                        serializer.get_state(default.get("input_machine_id"))
                    )
                    init_states.append(
                        serializer.get_state(default.get("proccessing_machine_id"))
                    )
                    init_states.append(
                        serializer.get_state(default.get("output_machine_id"))
                    )
                    tagmachine = TagMachine(init_states, timer, logger)
                    tag = Tag(environment, info[1], tagmachine, None, info[2:5])
                    objects[info[1]] = tag
                elif info[0] == "exciter":
                    exciter = Exciter(environment, "default", info[1:4])
                elif info[0] == "default":
                    default = parse_default(info[1:3], default, serializer)
                elif info[0] == "event":

                    event_args = {}
                    event_args["delay"] = int(info[1])
                    event_args["tag"] = info[2]
                    event_args["event_type"] = info[3]
                    i = 4
                    while i + 1 < len(info):
                        if info[i].lower() == "event_transmission":
                            event_args["transmission"] = info[i + 1]
                            i += 2
                        elif info[i].lower() == "event_mode":
                            event_args["mode"] = info[i + 1]
                            i += 2
                        else:
                            i += 1
                    new_event = EventArgs(**event_args)
                    times = [e.delay for e in events]
                    position = bisect.bisect_left(times, new_event.delay)
                    events.insert(position, new_event)

                elif info[0] == "load":
                    if os.path.exists(info[1]):
                        with open(info[1], "r") as f:
                            try:
                                raw_data = json.load(f)
                            except json.JSONDecodeError:
                                print("Skipping! invalid filepath:", info[1])
                        if raw_data.get("Format") == "state_machine":
                            states_output = load_states(raw_data, serializer, default)
                            if states_output is not None:
                                default = states_output
                        else:
                            print("Skipping! invalid format:", info[1])
            print(filepath, "successfully loaded")
            return exciter, objects, events, default


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

    # Temp
    environment = Environment(0)
    timer = "Temp"  # Remove later when timer/schedule is placed inside tags constructor
    ## TODO give tags their approriate tagmodes

    logger, q_listener = init_logger(logging.INFO)
    load_json(STATE_PATH, serializer)

    main_exciter, objects, events, default = load_json(
        CONFIG_PATH, serializer, timer=timer, logger=logger
    )

    _, _, events, _ = load_json(EVENT_PATH, serializer)

    machine_id_keys = [
        "input_machine_id",
        "proccessing_machine_id",
        "output_machine_id",
    ]
    machine_defined = not any(default[k] == "UNKOWN" for k in machine_id_keys)
    args = parse_args()

    # TODO Change this to take in arguments from the command line
    logger, q_listener = init_logger(logging.INFO)

    if args.load is not None:  # load in a file
        file_type = args.load.split(".")[-1]
        if file_type == "txt":
            if args.add:  # appends loaded arguments instead of overwrite
                temp_exciter, add_objects, add_events, add_default = load_txt(
                    args.load, environment, serializer, logger
                )
                objects.update(add_objects)
                default.update(add_default)
                events = list(heapq.merge(events, add_events, key=lambda x: x[0]))
            else:  # overwrites previouse saved data
                temp_exciter, objects, events, default = load_txt(
                    args.load, environment, serializer, logger
                )
            if temp_exciter is not None:
                main_exciter = temp_exciter
        elif file_type == "json":
            temp_exciter, temp_objects, temp_events, temp_default = load_json(
                args.load, serializer, default=default
            )
            if temp_objects is not None or temp_events is not None:
                objects = temp_objects
                events = temp_events
                default = temp_default
                main_exciter = temp_exciter
            elif temp_default is not None:
                default = temp_default
        else:
            print("error: file type not supported")
    if args.exciter:
        x, y, z = args.exciter[0:3]
        main_exciter = Exciter(environment, "default", (x, y, z))
        print("Exciter moved to ", x, y, z)
    if args.tag:
        if not machine_defined:
            print(
                "error: tags missing machine identification. \nuse following command to define them:"
                "\n--default [input,proccessing,output] init_state_id"
            )
            sys.exit(1)
        else:
            id, x, y, z = parse_obj(args.tag)
            init_states = []
            init_states.append(serializer.get_state(default.get("input_machine_id")))
            init_states.append(
                serializer.get_state(default.get("proccessing_machine_id"))
            )
            init_states.append(serializer.get_state(default.get("output_machine_id")))
            tagmachine = TagMachine(init_states, timer, logger)
            new_obj = Tag(Environment, id, tagmachine, "Listen", (x, y, z))
            objects[id] = new_obj
            print("Tag:", id, "moved to coordinates", x, y, z)

    if args.default is not None:  # updates default value
        default = parse_default(args.default, default, serializer=serializer)
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
                if main_exciter is not None:
                    print("Exciter:", main_exciter.to_dict())
                else:
                    print("Exciter: Undefined")
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
                for key, value in serializer.get_state_map().items():
                    print(f"{key}: {value.to_dict()}")

    # Events will be reconfigure later to work along side events.json
    if args.event:  # adds an event
        event = args.event
        if event[1] not in objects:
            print("error, unkown tag:", event[1])
        event_args = {}
        event_args["delay"] = int(event[0])
        event_args["tag"] = event[1]
        event_args["event_type"] = event[2]
        event_args["tag"] = event[1]
        if args.event_transmission:
            event_args["transmission"] = args.event_transmission[0]
        if args.event_mode:
            event_args["mode"] = args.event_mode[0]
        new_event = EventArgs(**event_args)
        times = [e.delay for e in events]
        position = bisect.bisect_left(times, new_event.delay)
        events.insert(position, new_event)
    save_config(main_exciter, objects, events, default, serializer)
    q_listener.stop()


if __name__ == "__main__":
    main()
