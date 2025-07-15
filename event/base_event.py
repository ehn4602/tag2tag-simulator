from abc import ABC
from typing import Any
from simpy.core import SimTime

from util.identifiers import id_generator


# TODO: Should add a hash function so it orders the same way if multiple events happen simultaneously
class EventArgs:
    """Represents an event loaded from the config which is the arguments to dispatch the event"""

    # TODO: convert event_type to enum
    event_type: str
    delay: SimTime
    args: dict

    def __init__(self, **kwargs):
        self.event_type = kwargs.pop("event_type")
        self.delay = kwargs.pop("delay")
        self.args = kwargs

    def __str__(self):
        return f"{self.event_type} at {self.delay}"

    def get_required_arg(self, arg_name: str) -> Any:
        value = self.get_arg(arg_name)
        if value is None:
            raise ValueError(
                f"{self}: Field {arg_name} is required, but no value was found."
            )
        return value

    def get_arg(self, arg_name: str) -> Any | None:
        return self.args.get(arg_name)

    def to_dict(self):
        return {"event_type": self.event_type, "delay": self.delay, **self.args}

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            event_type=data["event_type"],
            delay=data["delay"],
            **{k: v for k, v in data.items() if k not in ("event_type", "delay")},
        )


class Event(ABC):
    """Represents an implemented Event that can be run."""

    id_gen = id_generator()

    def __init__(self, args: EventArgs):
        super().__init__()
        self.id: int = next(Event.id_gen)
        self.event_type: str = args.event_type

    def run(self):
        raise NotImplementedError("Tag event wasn't implemented")

    def __str__(self):
        # TODO: add additional info for logging
        return f"Event.{self.event_type}{{id={self.id}}}"
