import json
from typing import List
from simpy import Environment
from event.base_event import Event, EventArgs
from event.event_types import EventTypes


def load_events() -> List[EventArgs]:
    """Read and sort events from config

    Returns:
        List[EventArgs]: The sorted EventArgs used for dispatching events
    """
    with open("config/events.json") as file:
        events: List = json.load(file)["Events"]
        events: List[EventArgs] = [EventArgs(**event) for event in events]
        # TODO sort by event.delay and then event.hash() or something

        events.sort(key=lambda event: event.delay)
        return events


def application_layer(env: Environment):
    """The top-level simpy process that oversees tag communication and represents external inputs

    Args:
        env (Environment): The simpy environment

    Yields:
        _type_: _description_
    """

    event_list: List[Event] = []
    events_args: List[EventArgs] = load_events()
    for events_args in events_args:
        delay = events_args.delay - env.now
        if delay > 0:
            yield env.timeout(delay=delay)
            print(f"\n---- time={env.now} ----")
        event: Event = EventTypes.create_event(events_args)
        event_list.append(event)
        EventTypes.dispatch_event(event)
