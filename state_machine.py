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


class State:
    def __init__(self):
        self.transitions = {}

    def add_transition(self, expect_input, method, state):
        self.transitions[expect_input] = (method, state)

    def follow_symbol(self, symbol):
        if symbol in self.transitions:
            return self.transitions[symbol]
        else:
            return None

    def does_accept_symbol(self, symbol):
        return symbol in self.transitions

    def to_dict(self, serializer):
        transitions_serialized = {}
        for expect_input, (method, state) in self.transitions.items():
            if isinstance(method, tuple):
                method_serialized = list(method)
            else:
                method_serialized = [method]

            transitions_serialized[expect_input] = [
                method_serialized,
                serializer._map_state_to_id(state),
            ]
        return {"transitions": transitions_serialized}

    @classmethod
    def from_dict(cls, id, data, serializer):
        state = serializer._map_id_to_state(id)
        for expect_input, (method, output_id) in data["transitions"].items():
            output_state = serializer._map_id_to_state(output_id)
            state.add_transition(expect_input, tuple(method), output_state)
        return state


class StateSerializer:

    def __init__(self):
        self.items = []
        self.mappings = {}

    def _map_state_to_id(self, state):
        if state in self.mappings:
            return self.mappings[state]
        else:
            id = len(self.items)
            self.mappings[state] = id
            self.items.append(state)
            return id

    def _map_id_to_state(self, id):
        while id >= len(self.items):
            sub_id = len(self.items)
            sub_state = State()
            self.items.append(sub_state)
            self.mappings[sub_state] = sub_id
        return self.items[id]

    def serialize(self, state):
        pass

    def to_dict(self):
        return [{"id": i, **state.to_dict(self)} for i, state in enumerate(self.items)]


class StateMachine:
    def __init__(self, init_state, id):
        self.state = init_state
        self.init_state = init_state
        self.id = id

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

    def to_dict(self, serializer, type):

        init_state_id = serializer._map_state_to_id(self.init_state)
        return {
            "id": self.id,
            "type": type,  # to be implemented
            "init_state": init_state_id,
        }

    @classmethod
    def from_dict(cls, serializer, data):
        init_state = serializer._map_id_to_state(data.get("init_state"))
        return StateMachine(init_state, data.get("id"))


class ExecuteMachine(StateMachine):
    def __init__(self, init_state, world_interface):
        super(self).__init__(init_state)
        self.world_interface = world_interface
        self.transition_queue = None

    def _accept_symbol(self, symbol):
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


class InputMachine(StateMachine):
    def __init__(self, init_state, world_interface, output_cb):
        super(self).__init__(init_state, world_interface)
        self.output_cb = output_cb
        self.last_voltage = None
        self.voltage = None

    def _cmd_set_timer(self, time):
        self.world_interface.set_timer(time)

    def _cmd_forward_voltage(self):
        self.output_cb("voltage", self.world_interface.read_voltage())

    def _cmd_test_voltage_change(self, threshold):
        pass

    def prepare(self):
        self.accept_symbol("init")

    def on_timer(self):
        self.last_voltage = self.voltage
        self.accept_symbol("on_timer")


class ProcessingMachine(StateMachine):
    def __init__(self, init_state, world_interface, output_cb, log_cb):
        super(self).__init__(init_state, world_interface)
        self.output_cb = output_cb
        self.log_cb = log_cb
        self.regs = [0 for _ in range(8)]
        self.recv = None

    def _cmd_send_int_out(self):
        self.output_cb("send_int", self.acc)

    def _cmd_send_int_log(self):
        self.log_cb("send_int", self.acc)

    def _cmd_mov(self):
        pass

    def prepare(self):
        self.accept_symbol("init")

    def on_timer(self):
        self.last_voltage = self.voltage
        self.accept_symbol("on_timer")


class TagMachine:
    def __init__(self, id, Coordinates):
        self.Coordinates = Coordinates
        self.id = id
        self.input_machine = None
        self.input_acc = 0
        self.processing_machine = None
        self.output_machine = None

    def follow_symbol(self, found_input):
        input_out = self.input_machine.transition(found_input)
        output_out = self.input_machine
        for input_out_ent in input_out:
            output_out
        if input_out[0][0] == "push_binary":
            pass

    def to_dict(self):

        # TODO implement solution to uknowns when default values are defined
        input_id, proccess_id, output_id = "Unknown", "Unknown", "Unknown"
        if isinstance(self.input_machine, str):
            input_id = self.input_machine
        elif self.input_machine is not None:
            input_id = self.input_machine.id
        if isinstance(self.processing_machine, str):
            proccess_id = self.processing_machine
        elif self.processing_machine is not None:
            proccess_id = self.processing_machine.id
        if isinstance(self.output_machine, str):
            output_id = self.output_machine
        elif self.output_machine is not None:
            output_id = self.output_machine.id
        return {
            "id": self.id,
            "x": self.Coordinates[0],
            "y": self.Coordinates[1],
            "z": self.Coordinates[2],
            "input_machine_id": input_id,
            "processing_machine_id": proccess_id,
            "output_machine_id": output_id,
        }

    @classmethod
    def from_dict(cls, id, data, stateMachines):
        Coords = [data.get("x"), data.get("y"), data.get("z")]
        tag = TagMachine(id, Coords)
        tag.input_machine = stateMachines.get(data.get("input_machine_id"))
        tag.processing_machine = stateMachines.get(data.get("processing_machine_id"))
        tag.output_machine = stateMachines.get(data.get("output_machine_id"))
        return tag
