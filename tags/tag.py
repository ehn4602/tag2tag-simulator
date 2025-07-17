from typing import List

from simpy import Environment

from tags.state_machine import TagMachine, TimerScheduler
from util.types import Position
from manager.tag_manager import TagManager


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


class PhysicsObject:
    """
    An object which interacts with the physics engine.
    """

    def __init__(
        self,
        env: Environment,
        name: str,
        pos: Position,
        power: float,
        gain: float,
        impedance: float,
        frequency: float,
    ):
        self.env = env
        self.name = name
        self.pos = pos
        self.power = power
        self.gain = gain
        self.impedance = impedance
        self.frequency = frequency

    def get_name(self):
        return self.name

    def get_position(self):
        return self.pos

    def get_power(self):
        return self.power

    def get_gain(self):
        return self.gain

    def get_impedance(self):
        return self.impedance

    def get_frequency(self):
        return self.frequency


class Exciter(PhysicsObject):
    """Class for Exciters"""

    def __init__(
        self,
        env: Environment,
        name: str,
        pos: Position,
        power: float,
        gain: float,
        impedance: float,
        frequency: float,
    ):
        super().__init__(env, name, pos, power, gain, impedance, frequency)

    def to_dict(self):
        """For placing exciters from dicts correctly to JSON"""
        return {
            "id": self.name,
            "x": self.pos[0],
            "y": self.pos[1],
            "z": self.pos[2],
            "power": self.power,
            "gain": self.gain,
            "impedance": self.impedance,
            "frequency": self.frequency,
        }

    @classmethod
    def from_dict(cls, environment, data):
        return Exciter(
            environment,
            data["id"],
            (data["x"], data["y"], data["z"]),
            data["power"],
            data["gain"],
            data["impedance"],
            data["frequency"],
        )


class Tag(PhysicsObject):
    """Class for Tags"""

    def __init__(
        self,
        env: Environment,
        tag_manager: TagManager,
        name: str,
        tag_machine: TagMachine,
        mode: TagMode,
        pos: Position,
        power: float,
        gain: float,
        impedance: float,
        frequency: float,
        reflection_coefficients: List[float],
    ):
        super().__init__(env, name, pos, power, gain, impedance, frequency)
        self.tag_manager = tag_manager
        self.tag_machine = tag_machine
        self.mode = mode
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
        return self.tag_manager.get_received_voltage(self)

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
        tag_manager: TagManager,
        logger,
        timer: TimerScheduler,
        name: str,
        data: dict,
        serializer,
        default: dict,
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
            env,
            tag_manager,
            name,
            tag_machine,
            TagMode.LISTENING,
            (
                data["x"],
                data["y"],
                data["z"],
            ),
            0,
            default["gain"],
            default["impedance"],
            default["frequency"],
            default["reflection_coefficients"],
        )
        tag_machine.set_tag(tag)
        return tag
