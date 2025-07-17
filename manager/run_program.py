from typing import Dict

from manager.application_layer import application_layer
from manager.tag_manager import TagManager
from state import AppState
from tags.tag import Exciter, Tag


# TODO: is default needed as an argument?
def run_program(
    app_state: AppState,
    main_exciter: Exciter,
    tags: Dict[str, Tag],
    events,
    default,
):
    app_state.set_tag_manager(TagManager(main_exciter, tags=tags))

    # TODO: add events
    # env.process(application_layer(env))
    for tag in tags.values():
        tag.run()

    app_state.env.run(until=100000)
