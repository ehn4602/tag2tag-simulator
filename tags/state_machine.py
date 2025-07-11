from typing import List, Optional, Dict
from abc import ABC, abstractmethod
from tag import Tag

import physics


# closer to pseudo code than an actual implementation
# will have to hash this out
class WorldInterface:
    def __init__(self, machine):
        self.machine = machine

    # called by a machine to set its antenna
    def set_antenna(self, setting):
        pass

    # called by something in the simulator to update a machine
    # when another machine adjusts its antenna
    def notify_update(self):
        pass

    # like notify_update, but called when a timer set by the machine
    # goes off
    def notify_timer(self):
        pass

    # set the time until a timer update comes in
    # time == None disables the timer
    def set_timer(self, time):
        pass

    # read the voltage at the envelope detector
    def read_voltage(self):
        pass


class PhysicsInterface:
    def __init__(self, engine: physics.PhysicsEngine):
        self.engine = engine

    def get_voltage(self) -> float:
        pass


class TimerScheduler(ABC):
    @abstractmethod
    def set_timer(self, delay: int):
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


class TimerBridgeChild(TimerScheduler):
    """
    Acts as a TimerAcceptor proxy for the last object to schedule a timer
    """

    parent: "TimerBridge"


class TimerBridge:
    """
    Acts as a TimerBridgeChild factory
    """

    timer_obj_last: Optional[TimerAcceptor]

    def __init__(self, world_interface: WorldInterface):
        self.world_interface = world_interface
        self.timer_obj_last = None

    def set_timer(self, obj: TimerAcceptor, timer_val):
        if timer_val is None:
            if self.timer_obj_last == obj:
                self.timer_obj_last = None
            self.world_interface.set_timer(None)
        else:
            self.timer_obj_last = obj
            self.world_interface.set_timer(timer_val)

    def on_timer(self):
        if self.timer_obj_last is not None:
            self.timer_obj_last.on_timer()


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


class ExecuteMachine(StateMachine):
    registers: List[int | float]

    def __init__(self, init_state, tag: Tag):
        super(self).__init__(init_state)
        self.tag = tag
        self.transition_queue = None
        self.registers = [0 for _ in range(8)]

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


class InputMachine(ExecuteMachine):
    def __init__(
        self, init_state, tag: Tag, timer: TimerScheduler, processing_machine: "ProcessingMachine"
    ):
        super(self).__init__(init_state, tag)
        self.processing_machine = processing_machine
        self.timer = timer

    def _cmd_set_timer(self, timer_reg):
        self.timer.set_timer(self.registers[timer_reg])

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
        self, init_state, tag: Tag, output: "OutputMachine", logger: "LoggerBase"
    ):
        super(self).__init__(init_state, tag)
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
        self.logger.log(self.registers[reg])


class OutputMachine(ExecuteMachine):
    def __init__(self, init_state, tag: Tag, timer: TimerScheduler):
        super(self).__init__(init_state, tag)
        self.timer = timer

    def _cmd_set_antenna(self, n: int):
        self.tag.set_mode_reflect(n)

    def _cmd_set_timer(self, time):
        self.timer.set_timer(time)

    def on_recv_int(self, n: int):
        self.registers[7] = n
        self._accept_symbol("on_recv_int")


class LoggerBase(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def log(self, out: str):
        pass


class TagMachine:
    def __init__(self, init_states, tag: Tag, timer: TimerScheduler, logger: LoggerBase):
        self.output_machine = OutputMachine(init_states[2], tag, timer)
        self.processing_machine = ProcessingMachine(
            init_states[1], tag, self.output_machine, logger
        )
        self.input_machine = InputMachine(
            init_states[0], tag, timer, self.processing_machine
        )
        self.timer_bridge = TimerBridge(world_interface)

    def prepare(self):
        self.input_machine.prepare()

    def on_timer(self):
        self.timer_bridge.on_timer()
    
    def to_dict(self):
        return {
            "input_machine": self.input_machine.to_dict(),
            "processing_machine": self.processing_machine.to_dict(),
            "output_machine": self.output_machine.to_dict()
            }
    
    @classmethod
    def from_dict(cls, tag: Tag, logger: LoggerBase, data):
        return cls((data["input_machine"], data["processing_machine"], data["output_machine"]), tag, logger)
