from abc import ABC
from typing import Callable, Dict

from event.event_parser import EventParser
from state import AppState
from util.identifiers import id_generator


class Event(ABC):
    """Represents an implemented Event that can be run."""

    id_gen = id_generator()

    def __init__(self, parser: EventParser):
        super().__init__()
        # id is only used for debugging purposes
        self.id: int = next(Event.id_gen)
        self.event_type: str = parser.event_type
        self.time: int = parser.time
        self.args: Dict = parser.args
        self.prepare_actions: Callable[[AppState]] = []

    def add_prepare_action(self, action: Callable[[AppState], None]):
        self.prepare_actions.append(action)

    def prepare(self, app_state: AppState):
        for action in self.prepare_actions:
            action(app_state)

    def run(self):
        raise NotImplementedError("Tag event wasn't implemented")

    def log_extra(self):
        """Return extra information for logging"""
        return {
            "event_type": self.event_type,
        }

    def __str__(self):
        return f"Event.{self.event_type}{{id={self.id}}}"

    def to_dict(self):
        """Convert the event to a dictionary representation."""
        return {
            "event_type": self.event_type,
            "time": self.time,
            **self.args,
        }
