from __future__ import annotations
from typing import TYPE_CHECKING
from simpy import Environment
from simpy.core import SimTime

if TYPE_CHECKING:
    from manager.tag_manager import TagManager


class AppState:
    def __init__(self):
        self.env: Environment = Environment()
        self.tag_manager: TagManager

    def set_tag_manager(self, tag_manager: TagManager):
        self.tag_manager = tag_manager

    def now(self) -> SimTime:
        return self.env.now

    def now_plus(self, delay: SimTime) -> SimTime:
        return self.env.now + delay
