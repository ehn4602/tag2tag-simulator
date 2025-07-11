from typing import Callable, Dict
from event.base_event import Event
from event.tag_event import TagSetModeEvent
from manager.application_layer import EventArgs

type CreateEvent = Callable[[EventArgs], Event]


class EventTypes:
    """A utility class for mapping event types and dispatching events"""

    event_types: Dict[str, CreateEvent] = {
        "tag_set_mode": TagSetModeEvent,
    }

    @classmethod
    def create_event(cls, event_args: EventArgs) -> Event:
        event_type: str = event_args.event_type
        creator: CreateEvent = EventTypes.event_types[event_type]
        return creator(event_args)

    @classmethod
    def dispatch_event(cls, event: Event):
        print(f"Running event: {event}.")
        event.run()
