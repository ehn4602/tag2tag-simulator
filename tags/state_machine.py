from __future__ import annotations

from typing import List, Optional, Dict, TYPE_CHECKING
from abc import ABC, abstractmethod
from logging import Logger

if TYPE_CHECKING:
  from tags.tag import Tag

import physics

class PhysicsInterface:
    def __init__(self, engine: physics.PhysicsEngine):
        self.engine = engine

    def get_voltage(self) -> float:
        pass


class TimerScheduler(ABC):
    @abstractmethod
    def set_timer(self, timer_acceptor: "TimerAcceptor", delay: int):
        """
        Schedules a timer event
        """
        pass


class TimerAcceptor:
    @abstractmethod
    def on_timer(self):
        """
        Called when a timer event goes off
        """
        pass


class State:
    def __init__(self, name: str):
        self.transitions = {}
        self.name = name

    def add_transition(self, expect_symbol: str, method, state: "State"):
        self.transitions[expect_symbol] = (method, state)

    def follow_symbol(self, symbol: str):
        if symbol in self.transitions:
            return self.transitions[symbol]
        else:
            return None

    def does_accept_symbol(self, symbol):
        return symbol in self.transitions

    def get_name(self):
        return self.name


class StateSerializer:
    states: Dict[str, State]

    def __init__(self):
        self.states = {}

    def get_state(self, name: str):
        if name not in self.states:
            self.states[name] = State(name)
        return self.states[name]

    def get_state_map(self):
        return self.states


class StateMachine:
    def __init__(self, init_state):
        self.state = init_state
        self.init_state = init_state

    def get_state(self):
        return self.state

    def get_init_state(self):
        return self.init_state

    def transition(self, symbol):
        out = self.state.follow_symbol(symbol)
        if out is None:
            return []
        self.state = out[1]
        if out[0][0] == "sequence":
            return out[1]
        else:
            return [out[0]]


class MachineLogger:
    def __init__(self, logger: Logger):
        self.store = ""
        self.logger = logger
    
    def log(self, s: str):
        newline_index = s.find("\n")
        while newline_index != -1:
            self.logger.info(self.store + s[:newline_index])
            self.store = ""
            s = s[newline_index + 1:]
            newline_index = s.find("\n")
        self.store += s


class ExecuteMachine(StateMachine):
    registers: List[int | float]

    def __init__(self, init_state):
        super(self).__init__(init_state)
        self.transition_queue = None
        self.registers = [0 for _ in range(8)]
    
    def set_tag(self, tag: Tag):
        """
        Must be called after __init__ and before anything else
        """
        self.tag = tag

    def _cmd_mov(self, dst, src):
        """
        Performs dst := src
        """
        self.registers[dst] = self.registers[src]

    def _cmd_load_imm(self, dst, val):
        """
        Performs dst := $val
        """
        self.registers[dst] = val

    def _cmd_sub(self, dst, a, b):
        """
        Performs dst := a - b
        """
        self.registers[dst] = self.registers[a] - self.registers[b]

    def _cmd_floor(self, a):
        """
        Performs a := int(a)
        """
        self.registers[a] = int(self.registers[a])

    def _cmd_compare(self, a, b):
        """
        Sends symbol "lt", "eq", or "gt" to self
        depending on whether a < b, a = b, or a > b respectively
        """
        a_val = self.registers[a]
        b_val = self.registers[b]
        sym = None
        if a_val < b_val:
            sym = "lt"
        elif a_val == b_val:
            sym = "eq"
        else:
            sym = "gt"
        self._accept_symbol(sym)

    def _accept_symbol(self, symbol):
        """
        Dispatches symbol reception events to _cmd_* methods
        """
        if self.transition_queue is None:
            self.transiton_queue = [symbol]
        else:
            self.transition_queue.append(symbol)
        while len(self.transition_queue) != 0:
            symbol = self.transition_queue[0]
            self.transition_queue = self.transition_queue[1:]
            for cmd in self.transition(symbol):
                (cmd_first, *cmd_rest) = cmd
                self["_cmd_" + cmd_first](*cmd_rest)
        self.transition_queue = None


class InputMachine(ExecuteMachine, TimerAcceptor):
    def __init__(
        self, init_state, timer: TimerScheduler, processing_machine: "ProcessingMachine"
    ):
        super(self).__init__(init_state)
        self.processing_machine = processing_machine
        self.timer = timer

    def _cmd_set_timer(self, timer_reg):
        self.timer.set_timer(self, self.registers[timer_reg])

    def _cmd_save_voltage(self, out_reg):
        self.registers[out_reg] = self.tag.read_voltage()

    def _cmd_send_bit(self, reg):
        self.processing_machine.on_recv_bit(self.registers[reg])

    def _cmd_forward_voltage(self):
        self.processing_machine.on_recv_voltage(self.world_interface.read_voltage())

    def prepare(self):
        self._accept_symbol("init")

    def on_timer(self):
        self._accept_symbol("on_timer")


class ProcessingMachine(ExecuteMachine):
    def __init__(
        self, init_state, output: "OutputMachine", logger: MachineLogger
    ):
        super(self).__init__(init_state)
        self.output = output
        self.logger = logger

    def on_recv_bit(self, val: bool):
        self.registers[7] = val and 1 or 0
        self._accept_symbol("on_recv_bit")

    def on_recv_voltage(self, val: float):
        self.registers[7] = val
        self._accept_symbol("on_recv_voltage")

    def _cmd_send_int_out(self, reg):
        self.output.on_recv_int(self.registers[reg])

    def _cmd_send_int_log(self, reg):
        self.logger.log(str(self.registers[reg]))


class OutputMachine(ExecuteMachine, TimerAcceptor):
    def __init__(self, init_state, timer: TimerScheduler):
        super(self).__init__(init_state)
        self.timer = timer

    def _cmd_set_antenna(self, n: int):
        self.tag.set_mode_reflect(n)
    
    def _cmd_set_listen(self):
        self.tag.set_mode_listen()

    def _cmd_set_timer(self, time):
        self.timer.set_timer(self, time)

    def on_recv_int(self, n: int):
        self.registers[7] = n
        self._accept_symbol("on_recv_int")


class TagMachine:
    def __init__(self, init_states, timer: TimerScheduler, logger: MachineLogger):
        self.output_machine = OutputMachine(init_states[2], timer)
        self.processing_machine = ProcessingMachine(
            init_states[1], self.output_machine, logger
        )
        self.input_machine = InputMachine(
            init_states[0], timer, self.processing_machine
        )

    def set_tag(self, tag: Tag):
        self.input_machine.set_tag(tag)
        self.processing_machine.set_tag(tag)
        self.output_machine.set_tag(tag)

    def prepare(self):
        self.input_machine.prepare()
    
    def to_dict(self):
        return {
            "input_machine": self.input_machine.init_state.to_dict(),
            "processing_machine": self.processing_machine.init_state.to_dict(),
            "output_machine": self.output_machine.init_state.to_dict()
            }
    
    @classmethod
    def from_dict(cls, timer: TimerScheduler, logger: MachineLogger, data):
        return cls((State.from_dict(data["input_machine"]), State.from_dict(data["processing_machine"]), State.from_dict(data["output_machine"])), timer, logger)
