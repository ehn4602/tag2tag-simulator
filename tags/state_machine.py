from __future__ import annotations

from typing import List, Optional, Self, Dict, Any, TYPE_CHECKING, Tuple
from abc import ABC, abstractmethod
import logging
from logging import Logger
import heapq

from simpy.core import SimTime
from simpy import Interrupt

from state import AppState

if TYPE_CHECKING:
    from tags.tag import Tag


class Timer:
    def __init__(self, timer_acceptor: "TimerAcceptor", next_run: SimTime):
        self._timer_acceptor = timer_acceptor
        self._next_run = next_run
        self._is_canceled = False

    def get_next_run(self):
        return self._next_run

    def cancel(self):
        self._is_canceled = True

    def is_canceled(self):
        return self._is_canceled

    def run(self):
        if not self.is_canceled():
            self._timer_acceptor.on_timer()
            self.cancel()

    def __lt__(self, other: Self) -> bool:
        return self._next_run < other._next_run


class TimerScheduler:

    def __init__(self, app_state: AppState):
        self.app_state: AppState = app_state
        self.timers: List[Timer] = []
        self.next_run: Optional[int] = None
        self.process = self.app_state.env.process(self.run())

    def run(self):
        while True:
            while (
                len(self.timers) != 0
                and self.timers[0].get_next_run() <= self.app_state.now()
            ):
                self.timers[0].run()
                heapq.heappop(self.timers)
            delay: SimTime
            if len(self.timers) == 0:
                self.next_run = None
                delay = float("inf")
            else:
                self.next_run = self.timers[0].get_next_run()
                delay = self.next_run - self.app_state.now()
            try:
                yield self.app_state.env.timeout(delay)
            except Interrupt:
                pass

    def set_timer(self, timer_acceptor: TimerAcceptor, delay: int) -> Timer:
        """
        Schedules a timer event
        """
        assert delay >= 0
        timer = Timer(timer_acceptor, self.app_state.now_plus(delay))
        heapq.heappush(self.timers, timer)
        if self.next_run is None or self.timers[0].get_next_run() < self.next_run:
            self.process.interrupt()
        return timer


# Maybe rename to TimerAccessor
class TimerAcceptor(ABC):
    def __init__(self, timer: TimerScheduler):
        self._scheduler = timer
        self._last_timer: Optional[Timer] = None

    def set_timer(self, delay: int):
        """
        Schedules a timer event
        """
        if self._last_timer is not None:
            self._last_timer.cancel()
            self._last_timer = None
        if delay != 0:
            self._last_timer = self._scheduler.set_timer(self, delay)
        # TODO: what about if delay is zero?
        # TODO: What about if delay is zero?

    @abstractmethod
    def on_timer(self):
        """
        Called when a timer event goes off
        """
        pass


class State:
    def __init__(self, name: str):
        self.transitions: dict[str, tuple[Any, State]] = {}
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

    @classmethod
    def _method_from_dict(cls, d):
        if isinstance(d, list):
            return tuple([cls._method_from_dict(x) for x in d])
        else:
            return d

    @classmethod
    def _method_to_dict(cls, method):
        if isinstance(method, tuple):
            return [cls._method_to_dict(x) for x in method]
        else:
            return method

    def to_dict(self):
        transitions_serialized = {}
        for expect_input, (method, state) in self.transitions.items():
            transitions_serialized[expect_input] = [
                self._method_to_dict(method),
                state.name,
            ]
        return {"id": self.name, "transitions": transitions_serialized}

    @classmethod
    def from_dict(cls, data, serializer: StateSerializer, id=None):
        if isinstance(data, str):
            return serializer.get_state(data)
        id = data.get("id")
        state = serializer.get_state(id)
        for expect_input, (method, output_id) in data["transitions"].items():
            output_state = serializer.get_state(output_id)
            state.add_transition(
                expect_input, cls._method_from_dict(method), output_state
            )
        return state


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

    def to_dict(self):
        return [{"id": state.name, **state.to_dict()} for state in self.states.values()]


class StateMachine:
    def __init__(self, init_state: State):
        self.state = init_state
        self.init_state = init_state

    def get_state(self):
        return self.state

    def get_init_state(self):
        return self.init_state

    def transition(self, symbol):
        out = self.state.follow_symbol(symbol)
        if out is None:
            return None
        self.state = out[1]
        return out[0]


class MachineLogger:
    def __init__(self, logger: Logger):
        self.store = ""
        self.logger = logger

    def log(self, s: str):
        newline_index = s.find("\n")
        while newline_index != -1:
            self.logger.info(self.store + s[:newline_index])
            self.store = ""
            s = s[newline_index + 1 :]
            newline_index = s.find("\n")
        self.store += s


class ExecuteMachine(StateMachine, TimerAcceptor):

    def __init__(self, tag_machine: TagMachine, init_state: State):
        super().__init__(init_state)
        self.tag_machine = tag_machine
        self.transition_queue: Optional[List[str]] = None
        self.registers: List[int | float] = [0 for _ in range(8)]

    def _cmd(self, cmd_first: str, cmd_rest: List):
        method_name = "_cmd_" + cmd_first

        # TODO: Convert to debug logging
        tag_name = self.tag_machine.tag.get_name()
        arguments = ",".join([str(arg) for arg in cmd_rest])
        logging.info(f"[{tag_name}] {method_name}({arguments})")

        getattr(self, method_name)(*cmd_rest)

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

    def _cmd_add(self, dst, a, b):
        """
        Performs dst := a + b
        """
        self.registers[dst] = self.registers[a] + self.registers[b]

    def _cmd_floor(self, a):
        """
        Performs a := int(a)
        """
        self.registers[a] = int(self.registers[a])

    def _cmd_abs(self, a):
        """
        Performs a := abs(a)
        """
        self.registers[a] = abs(self.registers[a])

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

    def _cmd__comment(self, *comment_lines: str):
        pass

    def _cmd_sequence(self, *cmd_list):
        for cmd in cmd_list:
            (cmd_first, *cmd_rest) = cmd
            self._cmd(cmd_first, cmd_rest)

    def _cmd_self_trigger(self, symbol):
        self._accept_symbol(symbol)

    def _cmd_set_timer(self, timer_reg):
        self.tag_machine.timer.set_timer(self, self.registers[timer_reg])

    def prepare(self):
        self._accept_symbol("init")

    def on_timer(self):
        self._accept_symbol("on_timer")

    def _accept_symbol(self, symbol):
        """
        Dispatches symbol reception events to _cmd_* methods
        """
        if self.transition_queue is None:
            self.transition_queue = [symbol]
        else:
            self.transition_queue.append(symbol)
            return
        while len(self.transition_queue) != 0:
            symbol = self.transition_queue[0]
            self.transition_queue = self.transition_queue[1:]
            cmd = self.transition(symbol)
            if cmd is not None:
                (cmd_first, *cmd_rest) = cmd
                self._cmd(cmd_first, cmd_rest)
        self.transition_queue = None


class InputMachine(ExecuteMachine):
    def __init__(self, tag_machine: TagMachine, init_state: State):
        super().__init__(tag_machine, init_state)

    def _cmd_save_voltage(self, out_reg):
        self.registers[out_reg] = self.tag_machine.tag.read_voltage()

    def _cmd_send_bit(self, reg):
        self.tag_machine.processing_machine.on_recv_bit(self.registers[reg] != 0)

    def _cmd_forward_voltage(self):
        self.tag_machine.processing_machine.on_recv_voltage(
            self.tag_machine.tag.read_voltage()
        )


class ProcessingMachine(ExecuteMachine):
    def __init__(self, tag_machine: TagMachine, init_state: State):
        super().__init__(tag_machine, init_state)
        self.tag_machine = tag_machine
        self.mem = [0 for _ in range(64)]

    def on_recv_bit(self, val: bool):
        self.registers[7] = val and 1 or 0
        self._accept_symbol("on_recv_bit")

    def on_recv_voltage(self, val: float):
        self.registers[7] = val
        self._accept_symbol("on_recv_voltage")

    def on_queue_up(self):
        self._accept_symbol("on_queue_up")

    def _cmd_send_int_out(self, reg):
        self.tag_machine.output_machine.on_recv_int(self.registers[reg])

    def _cmd_send_int_log(self, reg):
        self.tag_machine.logger.log(str(self.registers[reg]))

    def _cmd_store_mem_imm(self, reg_addr, imm):
        if isinstance(imm, tuple):
            imm = list(imm)
        else:
            imm = [imm]
        base_idx = self.registers[reg_addr]
        for idx in range(len(imm)):
            self.mem[base_idx + idx] = imm[idx]

    def _cmd_load_mem(self, dst, addr_reg):
        self.registers[dst] = self.mem[self.registers[addr_reg]]


class OutputMachine(ExecuteMachine, TimerAcceptor):
    def __init__(self, tag_machine: TagMachine, init_state: State):
        super().__init__(tag_machine, init_state)

    def _cmd_set_antenna(self, reg):
        self.tag_machine.tag.set_mode_reflect(self.registers[reg])

    def _cmd_set_listen(self):
        self.tag_machine.tag.set_mode_listen()

    def _cmd_set_timer(self, time):
        self.tag_machine.timer.set_timer(self, time)

    def _cmd_queue_processing(self):
        self.tag_machine.processing_machine.on_queue_up()

    def on_recv_int(self, n: int):
        self.registers[7] = n
        self._accept_symbol("on_recv_int")


class TagMachine:
    def __init__(
        self,
        app_state: AppState,
        init_states: Tuple[State, State, State],
        logger: Logger,
    ):
        self.timer = TimerScheduler(app_state)
        self.logger = MachineLogger(logger)
        self.input_machine = InputMachine(self, init_states[0])
        self.processing_machine = ProcessingMachine(self, init_states[1])
        self.output_machine = OutputMachine(self, init_states[2])
        self.tag: Tag

    def set_tag(self, tag: Tag):
        self.tag = tag

    def prepare(self):
        # can set antenna settings before everything else
        self.output_machine.prepare()
        self.input_machine.prepare()
        self.processing_machine.prepare()

    def to_dict(self):
        return {
            "input_machine": self.input_machine.init_state.name,
            "processing_machine": self.processing_machine.init_state.name,
            "output_machine": self.output_machine.init_state.name,
        }

    @classmethod
    def from_dict(cls, app_state: AppState, logger, data, serializer):
        return cls(
            app_state,
            (
                State.from_dict(data["input_machine"], serializer),
                State.from_dict(data["processing_machine"], serializer),
                State.from_dict(data["output_machine"], serializer),
            ),
            logger,
        )
