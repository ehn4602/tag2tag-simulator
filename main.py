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

CONFIG_PATH = "./config/config.json"


# TODO figure out how to format state machine as JSON
def load_json(file_input):
    """Loads config file, gaining information it needs to run

    Returns:
        tags,events,default: List of information thats stored in JSON file
    """

    DEFAULT_STATS = {"exciter_power": 500.0, "gain": 0.0, "resistive_load": 50}
    if os.path.exists(file_input):
        with open(file_input, "r") as f:
            raw_data = json.load(f)

        if raw_data.get("Format") == "config":
            raw_objects = raw_data.get("Objects", {})
            raw_events = raw_data.get("events", [])

            default = raw_data.get("Default")
            tags = {uid: Tag.from_dict(uid, val) for uid, val in raw_objects.items()}
            events = [event for event in raw_events]
            return None, tags, events, default
        elif raw_data.get("Format") == "input_machine":
            print("input machine loaded")
            return None, None, None, None  # Placeholder
        elif raw_data.get("Format") == "processing_machine":
            print("processing machine loaded")
            return None, None, None, None  # Placeholder
        elif raw_data.get("Format") == "output_machine":
            print("output machine loaded")
            return None, None, None, None  # Placeholder
        else:
            print("error: invalid JSON format")
            sys.exit(1)
    elif file_input == CONFIG_PATH:
        return None, {}, [], DEFAULT_STATS
    else:
        print("error: file doesn't exist")
        sys.exit(1)


def save_config(objects, events, default):
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
                "Objects": {uid: obj.to_dict() for uid, obj in objects.items()},
                "events": events,
            },
            f,
            indent=4,
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
    except ValueError:
        print("error: coordinates given are not numerical values")
        sys.exit(1)
    return uid, coords[0], coords[1], coords[2]


def parse_default(vals, default):
    try:
        val = float(vals[1])
        default[vals[0]] = val
    except ValueError:
        print("error: invalid values for default")
        sys.exit(1)
    return default


def parse_args():
    """Parses arguments, can be in any order

    Returns:
        ArgumentParser: Argument parser which holds values of which arguments where given
    """
    parser = argparse.ArgumentParser(description="Tag-to-Tag Network Simulator")
    (
        parser.add_argument(
            "--tag",
            nargs=4,
            metavar=("UID", "X", "Y", "Z"),
            required=False,
            help="place a tag with its Unique ID at coordinates X,Y,Z",
        ),
    )
    (
        parser.add_argument(
            "--exciter",
            nargs=4,
            metavar=("UID", "X", "Y", "Z"),
            required=False,
            help="place an exciter with its Unique ID at coordinates X,Y,Z",
        ),
    )
    parser.add_argument(
        "--remove", type=str, required=False, help="Remove a specific tag based on UID"
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
    machine, objects, events, default = load_json(CONFIG_PATH)
    args = parse_args()

    # TODO Change this to take in arguments from the command line
    logger, q_listener = init_logger(logging.INFO)

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
            machine, temp_objects, temp_events, temp_default = load_json(args.load)
            if (
                temp_objects is not None
                or temp_events is not None
                or temp_default is not None
            ):
                objects = temp_objects
                events = temp_events
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

    if args.print:  # prints out information
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

    # Events will be reconfigure lateer to work along side events.json
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
    save_config(objects, events, default)
    q_listener.stop()


if __name__ == "__main__":
    main()
