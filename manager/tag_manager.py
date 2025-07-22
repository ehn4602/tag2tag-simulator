from typing import Dict
from physics import PhysicsEngine
from tags.tag import Exciter, Tag


class TagManager:

    def __init__(self, exciter: Exciter, tags: Dict[str, Tag] = dict()):
        self.tags: Dict[str, Tag] = tags
        self.physics_engine = PhysicsEngine(exciter)

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
        # TODO: very simple mockup for now

        return self.physics_engine.voltage_at_tag(self.tags, asking_tag)
