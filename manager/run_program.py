from typing import Dict, List

from event.base_event import Event
from manager.tag_manager import TagManager
from state import AppState
from tags.tag import Exciter, Tag


# Made into a dedicated method in the case we want logging around this.
def dispatch_event(event: Event):
    event.run()


def run_events(app_state: AppState, events: List[Event]):
    """The top-level simpy process that oversees tag communication and represents external inputs"""
    # Prepare events with app_state
    for event in events:
        event.prepare(app_state)

    # Run the events
    env = app_state.env
    for event in events:
        delay = event.time - env.now
        if delay > 0:
            yield env.timeout(delay=delay)
        dispatch_event(event)


# TODO: is default needed as an argument?
def run_simulation(
    app_state: AppState,
    main_exciter: Exciter,
    tags: Dict[str, Tag],
    events: List[Event],
    default,
):
    app_state.set_tag_manager(TagManager(main_exciter, tags=tags))
    env = app_state.env

    env.process(run_events(app_state, events))

    # Start tag machines
    for tag in tags.values():
        tag.run()

    # Run the simulation
    env.run(until=100000)
