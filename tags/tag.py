import logging
from typing import Optional, Self

from state import AppState
from tags.state_machine import TagMachine
from util.app_logger import init_tag_logger
from util.types import Position


class TagMode:
    _LISTENING_IDX = 0

    LISTENING: "TagMode"

    def __init__(self, index: int):
        self._index = index

    def is_listening(self) -> bool:
        return self._index == TagMode._LISTENING_IDX

    def get_reflection_index(self) -> int:
        return self._index

    def log_extra(self) -> dict:
        if self.is_listening():
            return {"is_listening": True}
        return {
            "is_listening": False,
            "reflection_index": self.get_reflection_index(),
        }

    def from_data(mode_str: str, reflection_index: Optional[int]) -> Self:
        mode_str = mode_str.upper()
        match (mode_str):
            case "TRANSMIT":
                if reflection_index is not None:
                    return TagMode(reflection_index)
                raise ValueError("TRANSMIT mode requires a reflection_index")
            case "LISTEN":
                return TagMode.LISTENING
            case _:
                raise ValueError(f"Unknown TagMode: {mode_str}")


TagMode.LISTENING = TagMode(TagMode._LISTENING_IDX)


class PhysicsObject:
    """
    An object which interacts with the physics engine.
    """

    def __init__(
        self,
        app_state: AppState,
        name: str,
        pos: Position,
        power: float,
        gain: float,
        impedance: float,
        frequency: float,
    ):
        self.app_state = app_state
        self.name = name
        self.pos = tuple([float(p) for p in pos])
        self.power = power
        self.gain = gain
        self.impedance = impedance
        self.frequency = frequency

    def get_name(self):
        return self.name

    def get_position(self) -> Position:
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
        app_state: AppState,
        name: str,
        pos: Position,
        power: float,
        gain: float,
        impedance: float,
        frequency: float,
    ):
        super().__init__(app_state, name, pos, power, gain, impedance, frequency)

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
    def from_dict(cls, app_state: AppState, data):
        return Exciter(
            app_state,
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
        app_state: AppState,
        name: str,
        tag_machine: TagMachine,
        mode: TagMode,
        pos: Position,
        power: float,
        gain: float,
        impedance: float,
        frequency: float,
        reflection_coefficients: list[float],
    ):
        super().__init__(app_state, name, pos, power, gain, impedance, frequency)
        self.tag_machine = tag_machine
        self.mode = mode
        self.reflection_coefficients = reflection_coefficients
        self.logger: logging.LoggerAdapter = init_tag_logger(self)

    def __str__(self):
        return f"Tag={{{self.name}}}"

    def run(self):
        """
        Run this tag with simpy
        """
        self.tag_machine.prepare()

    def set_mode(self, tag_mode: TagMode):
        self.mode = tag_mode

        msg: str
        if self.mode.is_listening():
            msg = "Set mode to LISTENING"
        else:
            msg = f"Set mode to REFLECT with index {self.mode.get_reflection_index()}"
        self.logger.info(msg, extra={"mode": self.mode.log_extra()})

    def set_mode_listen(self):
        self.set_mode(TagMode.LISTENING)

    def set_mode_reflect(self, index: int):
        self.set_mode(TagMode(index))

    def get_mode(self):
        return self.mode

    def get_reflection_coefficient(self):
        index = self.get_mode().get_reflection_index()
        return self.reflection_coefficients[index]

    def read_voltage(self) -> float:
        tag_manager = self.app_state.tag_manager
        voltage = tag_manager.get_received_voltage(self)
        self.logger.info(
            f"Read voltage: {voltage}",
            extra={"voltage": voltage},
        )
        return voltage

    def to_dict(self):
        """For placing tags into dicts correctly on JSON"""

        # TODO what if self.power was set to default?
        return {
            "tag_machine": self.tag_machine.to_dict(),
            "x": self.pos[0],
            "y": self.pos[1],
            "z": self.pos[2],
            "power": self.power,
            "gain": self.gain,
            "impedance": self.impedance,
            "frequency": self.frequency,
            "reflection_coefficients": self.reflection_coefficients,
        }

    @classmethod
    def from_dict(
        cls,
        app_state: AppState,
        logger,
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
            app_state, logger, data["tag_machine"], serializer
        )
        tag = cls(
            app_state,
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
