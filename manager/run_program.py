from typing import Dict

from manager.application_layer import application_layer
from manager.tag_manager import TagManager
from state import AppState
from tags.tag import Exciter, Tag


def run_program(
    app_state: AppState,
    main_exciter: Exciter,
    tags: Dict[str, Tag],
    events,
    default,
):
    # TODO: make this an instance field rather than static
    app_state.set_tag_manager(TagManager(main_exciter, tags=tags))
    env = app_state.env

    # def test_inf_timeout():
    #     print("Setup for delayed inf timeout test")
    #     yield env.timeout(1)
    #     print("Waiting forever")
    #     yield env.timeout(float("inf"))
    #     print("Forever passed")

    # env.process(test_inf_timeout())
    # env.process(application_layer(env))
    for tag in tags.values():
        tag.run()

    env.run(until=100000)
