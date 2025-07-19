from typing import Callable, Dict
from event.base_event import Event
from event.tag_event import TagSetModeEvent

from event.event_parser import EventParser

type CreateEvent = Callable[[EventParser], Event]


class EventTypes:
    """A utility class for mapping event types and dispatching events"""

    event_types: Dict[str, CreateEvent] = {
        "tag_set_mode": TagSetModeEvent,
    }

    def create_event(event_parser: EventParser) -> Event:
        event_type: str = event_parser.event_type.lower()
        creator: CreateEvent = EventTypes.event_types[event_type]
        return creator(event_parser)
