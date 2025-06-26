from simpy import Environment, Interrupt
import simpy


class Tag:
    def __init__(self, env: Environment, tag_manager: TagManager):
        self.env = env
        self.action = env.process(self.listen())

    def listen(self):
        # Maybe should be yield self.action?
        yield self.listen()


env: Environment = Environment()

transmitter_tag = Tag(env)
reciever_tag = Tag(env)

env.process(transmitter_tag)
env.process(reciever_tag)

env.run(until=100)
