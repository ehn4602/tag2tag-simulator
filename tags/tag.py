from enum import StrEnum, auto
from typing import List, Self
import uuid

from simpy import Environment

from abc import ABC, abstractmethod

from util.types import Position
from tags.state_machine import TagMachine, TimerScheduler, MachineLogger


class TagMode(ABC):
    @abstractmethod
    def is_listening(self) -> bool:
        pass


class TagModeListen(TagMode):
    def is_listening(self):
        return True


class TagModeReflect(TagMode):
    def __init__(self, index: int):
        self.index = index

    def is_listening(self):
        return False

    def get_index(self):
        return self.index


class Positionable:
    """A Tag or Exciter which can be moved around"""

    def __init__(self, env: Environment, name: str, pos: Position):
        self.env = env
        self.name = name
        self.pos = pos

    def get_name(self):
        return self.name

    def get_position(self):
        return self.pos


class Exciter(Positionable):
    """Class for Exciters"""

    def __init__(self, env: Environment, name: str, pos: Position):
        return super().__init__(env, name, pos)

    def to_dict(self):
        """For placing exciters from dicts correctly to JSON"""
        return {
            "id": self.name,
            "x": self.pos[0],
            "y": self.pos[1],
            "z": self.pos[2],
        }

    @classmethod
    def from_dict(cls, environment, data):
        return Exciter(environment, data["id"], (data["x"], data["y"], data["z"]))


class Tag(Positionable):
    """Class for Tags"""

    def __init__(
        self,
        env: Environment,
        name: str,
        tag_machine: TagMachine,
        mode: TagMode,
        pos: Position,
    ):
        super().__init__(env, name, pos)
        self.tag_machine = tag_machine
        self.mode = mode
        self.power = 0
        self.gain = 0
        self.resistance = 0

    def __str__(self):
        return f"Tag={{{self.name}}}"

    def run(self):
        """
        Run this tag as a simpy
        """

    def set_mode(self, tag_mode: TagMode):
        self.mode = tag_mode

    def set_mode_listen(self):
        self.set_mode(TagModeListen())

    def set_mode_reflect(self, index: int):
        self.set_mode(TagModeReflect(index))

    def get_mode(self):
        return self.mode

    def read_voltage(self) -> float:
        pass

    def to_dict(self):
        """For placing tags into dicts correctly on JSON"""
        return {
            "tag_machine": self.tag_machine.to_dict(),
            "x": self.pos[0],
            "y": self.pos[1],
            "z": self.pos[2],
            "x": self.pos[0],
            "y": self.pos[1],
            "z": self.pos[2],
        }

    @classmethod
    def from_dict(
        cls,
        env: Environment,
        logger,
        timer: TimerScheduler,
        name: str,
        data,
        serializer,
    ):
        """Creates a tag object from a JSON input

        Args:
            name (string): Unique name for tag
            data (list): list of Coordinates

        Returns:
            tag: returns tag loaded from JSON
        """
        tag_machine = TagMachine.from_dict(
            timer, logger, data["tag_machine"], serializer
        )
        tag = cls(
            env, name, tag_machine, TagModeReflect(0), (data["x"], data["y"], data["z"])
        )
        tag_machine.set_tag(tag)
        return tag
