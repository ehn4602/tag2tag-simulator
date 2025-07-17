from __future__ import annotations

from typing import TYPE_CHECKING

from tags.tag import Exciter, Tag

import physics

if TYPE_CHECKING:
    pass


class TagManager:
    # TODO: convert from static field
    tag_manager: TagManager

    def __init__(self, exciter: Exciter, tags=dict()):
        self.tags = tags
        self.physics_engine = physics.PhysicsEngine(exciter)

    def add_tags(self, *tags: Tag) -> None:
        """
        Register one or more tags with the TagManager for any future references

        Args:
            tag (Tag) -- The tag to register
        """
        for tag in tags:
            self.tags[tag.name] = tag

    def remove_by_name(self, *names: str) -> None:
        """
        Remove one or more tags by name from the TagManager

        Args:
            names (str) -- The names to remove from the tags dictionary
        """
        for name in names:
            self.tags.pop(name)

    def get_by_name(self, name: str) -> Tag:
        tag = self.tags[name]
        if tag is None:
            raise ValueError(f"{name}: Tag by this name does not exist!")
        return tag

    def get_received_voltage(self, asking_tag: Tag):
        # very simple mockup for now

        return self.physics_engine.voltage_at_tag(self.tags, asking_tag)
