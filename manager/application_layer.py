import json
from typing import Dict, List, Self
from simpy import Environment
from event.base_event import Event, EventArgs
from event.event_types import EventTypes


def load_events() -> List[EventArgs]:
    """Read and sort events from config

    Returns:
        List[EventArgs]: The sorted EventArgs used for dispatching events
    """

    with open("config/events.json") as file:
        events: List[Dict] = json.load(file)
        return [EventArgs(**event) for event in events]


class SortableEvent:
    def __init__(self, event: EventArgs):
        self.event = event
        self.event_type: str = event.event_type.casefold()

        event_args_json = json.dumps(event.args, sort_keys=True)
        self.args_hash = hash(event_args_json)

    def __lt__(self, other: Self) -> bool:
        # Order by delay
        diff = self.event.time - other.event.time
        if diff != 0:
            return diff < 0

        # Order by event_type
        if self.event_type != other.event_type:
            return self.event_type < other.event_type

        # Order by args hash
        return self.args_hash < other.args_hash


def init_events() -> List[Event]:
    events_args: List[EventArgs] = load_events()
    sortable_events: List[SortableEvent] = [SortableEvent(e) for e in events_args]
    sorted_events: List[SortableEvent] = [e.event for e in sorted(sortable_events)]
    return [EventTypes.create_event(args) for args in sorted_events]


def application_layer(env: Environment):
    """The top-level simpy process that oversees tag communication and represents external inputs

    Args:
        env (Environment): The simpy environment

    Yields:
        _type_: _description_
    """

    events = init_events()
    for event in events:
        delay = event.time - env.now
        if delay > 0:
            yield env.timeout(delay=delay)
        EventTypes.dispatch_event(event)
