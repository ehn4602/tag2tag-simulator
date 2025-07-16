from enum import StrEnum, auto
from typing import List, Self
import uuid

from simpy import Environment

from abc import ABC, abstractmethod

from util.types import Position
from tags.state_machine import TagMachine, TimerScheduler, MachineLogger


class TagMode:
    _LISTENING_IDX = 0

    LISTENING: "TagMode"

    def __init__(self, index: int):
        self._index = index

    def is_listening(self) -> bool:
        return self._index == TagMode._LISTENING_IDX

    def get_reflection_index(self) -> int:
        return self._index


TagMode.LISTENING = TagMode(TagMode._LISTENING_IDX)


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

    def __init__(
        self,
        env: Environment,
        name: str,
        pos: Position,
        power: float,
        gain: float,
        impedence: float,
    ):
        super().__init__(env, name, pos)
        self.power = power
        self.gain = gain
        self.impedence = impedence

    def to_dict(self):
        """For placing exciters from dicts correctly to JSON"""
        return {
            "id": self.name,
            "x": self.pos[0],
            "y": self.pos[1],
            "z": self.pos[2],
            "power": self.power,
            "gain": self.gain,
            "impedence": self.impedence,
        }

    @classmethod
    def from_dict(cls, environment, data):
        return Exciter(
            environment,
            data["id"],
            (data["x"], data["y"], data["z"]),
            data["power"],
            data["gain"],
            data["impedence"],
        )


class Tag(Positionable):
    """Class for Tags"""

    def __init__(
        self,
        env: Environment,
        name: str,
        tag_machine: TagMachine,
        mode: TagMode,
        pos: Position,
        reflection_coefficients: List[float],
    ):
        super().__init__(env, name, pos)
        self.tag_machine = tag_machine
        self.mode = mode
        self.power = 0
        self.gain = 0
        self.resistance = 0
        self.reflection_coefficients = reflection_coefficients

    def __str__(self):
        return f"Tag={{{self.name}}}"

    def run(self):
        """
        Run this tag as a simpy
        """

    def set_mode(self, tag_mode: TagMode):
        self.mode = tag_mode

    def set_mode_listen(self):
        self.set_mode(TagMode.LISTENING)

    def set_mode_reflect(self, index: int):
        self.set_mode(TagMode(index))

    def get_mode(self):
        return self.mode

    def get_reflection_coefficient(self):
        return self.reflection_coefficients[self.get_mode().get_reflection_index()]

    def read_voltage(self) -> float:
        pass

    def to_dict(self):
        """For placing tags into dicts correctly on JSON"""
        return {
            "tag_machine": self.tag_machine.to_dict(),
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
            env, name, tag_machine, TagMode.LISTENING, (data["x"], data["y"], data["z"])
        )
        tag_machine.set_tag(tag)
        return tag
