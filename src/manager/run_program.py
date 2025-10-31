import logging

from event.base_event import Event
from manager.tag_manager import TagManager
from state import AppState
from tags.tag import Exciter, Tag

# Made into a dedicated method in the case we want logging around this.
def dispatch_event(event: Event):
    logging.info(f"Event dispatched: {event.event_type}", extra=event.log_extra())
    event.run()


def run_events(app_state: AppState, events: list[Event]):
    """
    The top-level simpy process that oversees tag communication and represents external inputs.

    Args:
        app_state (AppState): The app state.
        events (list[Event]): The list of events to run.
    """
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
    exciters: dict[str, Exciter],
    tags: dict[str, Tag],
    events: list[Event],
    default,
):
    """
    Run the simulation.

    Args:
        app_state (AppState): The app state.
        exciters (dict[str, Exciter]): A dictionary of exciters.
        tags (dict[str, Tag]): A dictionary of tags to simulate, indexed by tag name.
        events (list[Event]): A list of events to simulate.
        default (Any): Default values, currently unused.
    """
    app_state.set_tag_manager(
        TagManager(
            exciters=exciters, tags=tags, passive_ref_mag=default["passive_ref_mag"]
        )
    )
    env = app_state.env

    env.process(run_events(app_state, events))

    # Start tag machines
    for tag in tags.values():
        tag.run()
    
    # Run the simulation
    env.run(until=500)
    