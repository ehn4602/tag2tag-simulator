from physics import PhysicsEngine
from tags.tag import Exciter, Tag


class TagManager:
    """
    A store of Tag instances, along with Exciters.
    """

    def __init__(self, exciters: dict[str, Exciter], tags: dict[str, Tag] = dict()):
        """
        Creates a TagManager.

        Args:
            exciters (dict[str, Exciter]): A dictionary mapping exciter names to Exciter instances.
            tags (dict[str, Tag]): A dictionary mapping tag names to Tag instances.
        """
        self.tags: dict[str, Tag] = tags
        self.physics_engine = PhysicsEngine(exciters)

    def add_tags(self, *tags: Tag) -> None:
        """
        Register one or more tags with the TagManager for any future references

        Args:
            tag (Tag): The tag to register
        """
        for tag in tags:
            self.tags[tag.name] = tag

    def remove_by_name(self, *names: str) -> None:
        """
        Remove one or more tags by name from the TagManager

        Args:
            names (str): The names to remove from the tags dictionary
        """
        for name in names:
            self.tags.pop(name)

    def get_by_name(self, name: str) -> Tag:
        """
        Retreive a Tag by name. Raises a ValueError if the tag doesn't exist.

        Args:
            name (str): The tag name.
        """
        tag = self.tags[name]
        if tag is None:
            raise ValueError(f"{name}: Tag by this name does not exist!")
        return tag

    def get_received_voltage(self, asking_tag: Tag) -> float:
        """
        Retrieve the voltage received by a tag.

        Args:
            name (str): The tag name.

        Returns:
            voltate (float): The received voltage.
        """
        return self.physics_engine.voltage_at_tag(self.tags, asking_tag)
