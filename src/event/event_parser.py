from typing import Any, overload
from simpy.core import SimTime

from state import AppState
from tags.tag import Tag

type ArgParseConditions = list[tuple[bool, str]]


class EventParser:
    """
    Represents the data for an event loaded from a config file.
    """

    def __init__(self, **kwargs):
        self.event_type: str = kwargs.pop("event_type").casefold()
        self.time: SimTime = kwargs.pop("time")
        self.args: dict = kwargs

    def __str__(self):
        return f"Event.{self.event_type} at t={self.time}"

    def get_required_tag(self, app_state: AppState, tag_arg: str, arg_name: str) -> Any:
        tag: Tag = app_state.tag_manager.get_by_name(tag_arg)
        if tag is None:
            raise ValueError(
                f"{self}: references unknown tag for {arg_name} field. Found {tag_arg}"
            )
        return tag

    # Not None
    def get_required_arg(self, arg_name: str) -> Any:
        return self.get_conditional_arg(arg_name)

    @overload
    def get_conditional_arg(
        self, arg_name: str, conditions: ArgParseConditions
    ) -> Any | None: ...

    def get_conditional_arg(
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
