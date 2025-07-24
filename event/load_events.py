import json
from typing import Self
from event.base_event import Event
from event.event_parser import EventParser
from event.event_types import EventTypes


class SortableEvent:

    def __init__(self, event: Event):
        self.event: Event = event
        self.event_type: str = event.event_type.casefold()

        event_json: str = json.dumps(event.args, sort_keys=True)
        self.args_hash: int = hash(event_json)

    def __lt__(self, other: Self) -> bool:
        # Order by delay
        if self.event.time != other.event.time:
            return self.event.time < other.event.time

        # Order by event_type
        if self.event_type != other.event_type:
            return self.event_type < other.event_type

        # Order by args hash
        return self.args_hash < other.args_hash


def load_event(event_data: dict) -> Event:
    event_parser = EventParser(**event_data)
    return EventTypes.create_event(event_parser)


def load_events(raw_data: list[dict]) -> list[Event]:
    events: list[Event] = [load_event(data) for data in raw_data]
    return sort_events(events)


def sort_events(events: list[Event]) -> list[Event]:
    """Sorts events by their time, type, and args hash."""
    sortable_events = [SortableEvent(e) for e in events]
    sorted_events = sorted(sortable_events)
    return [e.event for e in sorted_events]
