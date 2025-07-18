from abc import ABC
from typing import Any, List, Tuple, overload
from simpy.core import SimTime

from util.identifiers import id_generator

type ArgParseConditions = List[Tuple[bool, str]]


class EventArgs:
    """Represents an event loaded from the config which is the arguments to dispatch the event"""

    def __init__(self, **kwargs):
        self.event_type: str = kwargs.pop("event_type").casefold()
        self.time: SimTime = kwargs.pop("time")
        self.args: dict = kwargs

    def __str__(self):
        return f"Event.{self.event_type} at t={self.time}"

    # Overloaded just for the type annotation that this will not ever return None
    @overload
    def get_required_arg(self, arg_name: str) -> Any: ...

    @overload
    def get_required_arg(
        self, arg_name: str, conditions: ArgParseConditions
    ) -> Any | None: ...

    def get_required_arg(
        self,
        arg_name: str,
        conditions: ArgParseConditions | None = None,
    ) -> Any | None:
        value = self.get_arg(arg_name)
        if value is not None:
            return value

        if conditions is None:
            error_msg = f"{self}: Field {arg_name} is required, but no value was found"
            raise ValueError(error_msg)

        for condition in conditions:
            if not condition[0]:
                continue
            error_msg = f"{self}: Field {arg_name} is required when {condition[1]}, but no value was found"
            raise ValueError(error_msg)
        return None

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
        self.time: int = args.time

    def run(self):
        raise NotImplementedError("Tag event wasn't implemented")

    def __str__(self):
        return f"Event.{self.event_type}{{id={self.id}}}"
