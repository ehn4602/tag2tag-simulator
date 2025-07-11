from simpy import Environment
from manager.application_layer import application_layer
from manager.tag_manager import TagManager
from placeholder.tag import Tag


if __name__ == "__main__":
    env: Environment = Environment()

    env.process(application_layer(env))

    # Create and register tags
    transmitter_tag = Tag(env, name="mercury")
    reciever_tag = Tag(env, name="venus")
    TagManager.register(transmitter_tag, reciever_tag)

    env.run(until=100000)
