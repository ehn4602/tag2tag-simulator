import logging
import random

from manager.feedback_loop import FeedbackLoop
from event.base_event import Event
from manager.tag_manager import TagManager
from state import AppState
from tags.tag import Exciter, Tag


STEP_TIME = 1e-3  # 1 ms per simulation step (adjust as needed)
SIM_TIME = 1      # total simulation time in seconds (example)
NOISE_STD = 0.01  # noise standard deviation (adjustable)

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
    main_exciter: Exciter,
    tags: dict[str, Tag],
    events: list[Event],
    default,
):
    """
    Run the simulation.

    Args:
        app_state (AppState): The app state.
        main_exciter (Exciter): An exciter.
        tags (dict[str, Tag]): A dictionary of tags to simulate, indexed by tag name.
        events (list[Event]): A list of events to simulate.
        default (Any): Default values, currently unused.
    """
    app_state.set_tag_manager(TagManager(main_exciter, tags=tags))
    env = app_state.env

    env.process(run_events(app_state, events))

    # Start tag machines
    for tag in tags.values():
        tag.run()

    feedback_loop = FeedbackLoop(
        tag_manager=app_state.tag_manager,
        exciter=main_exciter,
        noise_std=NOISE_STD,
    )

    # Start dynamic tag loop to allow tags to communicate with each other
    env.process(feedback_loop_process(env, feedback_loop, STEP_TIME))

    # Run the simulation
    env.run(until=SIM_TIME)

def feedback_loop_process(env, feedback_loop, step_time):

    while True:
        feedback_loop.step()       # run one tick
        yield env.timeout(step_time)  # wait for next tick
    