from typing import Dict
from simpy import Environment

from manager.application_layer import application_layer
from manager.tag_manager import TagManager
from tags.tag import Tag


def run_program(env: Environment, main_exciter, tags: Dict[str, Tag], events, default):
    tag_manager = TagManager(main_exciter, tags=tags)
    
    env.process(application_layer(env))
    for tag in tags.values():
        tag.run()
    

    env.run(until=100000)
