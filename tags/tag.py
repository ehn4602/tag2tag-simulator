from __future__ import annotations

from typing import List, Optional, Self, Any

from state import AppState
from tags.state_machine import TagMachine
from util.types import Position


class TagMode:
    """
    A mode which a tag's antenna can be in. This is a wrapper for an index
    into a tag's antenna reflection coefficient table. It is assumed that 0
    refers to a connection to the envelope detector, or "listening mode".
    """

    _LISTENING_IDX = 0

    LISTENING: "TagMode"

    def __init__(self, index: int):
        """
        Initializes a TagMode

        Args:
            index (int): Antenna index.
        """
        self._index = index

    def is_listening(self) -> bool:
        """
        Returns:
            is_listening (bool): True if this tag mode refers to a listening configuration.
        """
        return self._index == TagMode._LISTENING_IDX

    def get_reflection_index(self) -> int:
        """
        Returns:
            index (int): Returns the antenna index associated with this mode.
        """
        return self._index

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
    An object which interacts with the physics engine. Used as a base class
    for Exciter and Tag.
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
        """
        Creates a PhysicsObject.

        Args:
            app_state (AppState): The AppState.
            name (str): The name of this physics object.
            pos (Position): The position of this physics object.
            power (float): Power.
            gain (float): Gain.
            impedance (float): Impedance.
            frequency (float): Frequency.
        """
        self.app_state = app_state
        self.name = name
        self.pos = tuple([float(p) for p in pos])
        self.power = power
        self.gain = gain
        self.impedance = impedance
        self.frequency = frequency

    def get_name(self) -> str:
        """
        Returns:
            name (str): The name of this physics object.
        """
        return self.name

    def get_position(self) -> Position:
        return self.pos

    def get_power(self):
        """
        Returns:
            power (float): Power.
        """
        return self.power

    def get_gain(self):
        """
        Returns:
            gain (float): Gain.
        """
        return self.gain

    def get_impedance(self):
        """
        Returns:
            impedance (float): Impedance.
        """
        return self.impedance

    def get_frequency(self):
        """
        Returns:
            frequency (float): Frequency.
        """
        return self.frequency


class Exciter(PhysicsObject):
    """An exciter object, which transmits a signal backscattering tags can reflect"""

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
        """
        Creates a PhysicsObject.

        Args:
            app_state (AppState): The AppState.
            name (str): The name of this exciter.
            pos (Position): The position of this exciter.
            power (float): Power.
            gain (float): Gain.
            impedance (float): Impedance.
            frequency (float): Frequency.
        """
        super().__init__(app_state, name, pos, power, gain, impedance, frequency)

    def to_dict(self) -> Any:
        """
        Converts an exciter object into a form that can be stored as JSON

        Returns:
            out (Any): Data storable as JSON.
        """
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
    def from_dict(cls, app_state: AppState, data: Any) -> Exciter:
        """
        Converts data loaded from JSON into a new Exciter object.

        Args:
            app_state (AppState): The app state.
            data (Any): Data loaded from JSON.
        """
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
    """
    An object representing a backscattering tag.
    """

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
        """
        Creates a Tag.

        Args:
            app_state (AppState): The app state.
            name (str): The name of this tag.
            tag_machine (TagMachine): The TagMachine associated with this tag.
            mode (TagMode): The initial mode this tag's antenna starts in.
            pos (Position): The position of this tag.
            power (float): Power.
            gain (float): Gain.
            impedance (float): Impedance.
            frequency (float): Frequency.
            reflection_coefficients (list[float]): A list that can be used to look up reflection coefficients by antenna index.
        """
        super().__init__(app_state, name, pos, power, gain, impedance, frequency)
        self.tag_machine = tag_machine
        self.mode = mode
        self.reflection_coefficients = reflection_coefficients

    def __str__(self):
        return f"Tag={{{self.name}}}"

    def run(self):
        """
        Run this tag with simpy
        """
        self.tag_machine.prepare()

    def set_mode(self, tag_mode: TagMode):
        self.mode = tag_mode

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
        return tag_manager.get_received_voltage(self)

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
        app_state: AppState,
        logger,
        name: str,
        data: dict,
        serializer,
        default: dict,
    ):
        """
        Creates a tag object from a JSON input

        Args:
            env (Environment): SimPy environment
            tag_manager (TagManager): Tag manager
            logger:
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
