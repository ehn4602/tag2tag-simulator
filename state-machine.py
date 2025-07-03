class State:
  def __init__(self):
    self.transitions = {}

  def add_transition(self, expect_input, method, state):
    self.transitions[expect_input] = (method, state)

  def follow_symbol(self, found_input);
    if found_input in self.transitions:
      return self.transitions[found_input]
    else:
      return self

class StateMachine:
  def __init__(self):
    self.state = State()

  def get_state(self):
    return self.state

  def transition(self, found_input):
    out = self.state.follow_symbol(found_input)
    self.state = out[1]
    if out[0][0] == "sequence":
      return out[1]
    else:
      return [out[0]]

class TagMachine:
  def __init__(self):
    self.input_machine = StateMachine()
    self.input_acc = 0;
    self.processing_machine = StateMachine()
    self.output_machine = StateMachine()

  def follow_symbol(self, found_input):
    input_out = self.input_machine.transition(found_input)
    output_out = self.input_machine
    for input_out_ent in input_out:
      output_out
    if input_out[0][0] == "push_binary":
