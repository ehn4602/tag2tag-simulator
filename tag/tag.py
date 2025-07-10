from enum import StrEnum, auto
from typing import List, Self
import uuid

from simpy import Environment


class TagMode(StrEnum):
    LISTEN = auto()
    TRANSMIT = auto()

    converter: dict

    @classmethod
    def from_str(cls, target: str) -> Self | None:
        if not hasattr(cls, "converter"):
            cls.converter = dict()
            for mode in TagMode:
                cls.converter[mode.casefold()] = mode
        # Use get to prevent error
        return cls.converter.get(target.casefold())


class Tag:
    """Placeholder class for Tags"""

    def __init__(self, env: Environment, name: str):
        self.env: Environment = env
        self.name: str = name
        self.id: int

    def __str__(self):
        return f"Tag={{{self.name}}}"

    def set_id(self, id):
        self.id = id

    def set_mode(self, tag_mode: TagMode):
        pass

    def set_transmission(self, transmission: List[int]):
        pass
