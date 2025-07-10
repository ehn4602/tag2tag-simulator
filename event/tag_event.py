from typing import List
from event.base_event import Event, EventArgs
from manager.tag_manager import TagManager
from placeholder.tag import Tag, TagMode


class TagEvent(Event):
    def __init__(self, args: EventArgs):
        super().__init__(args)
        self.tag: Tag = self._parse_tag(args)

    def _parse_tag(self, args: EventArgs) -> Tag:
        tag: str = args.get_required_arg("tag")
        tag: Tag = TagManager.get_by_name(tag)
        if tag is None:
            raise ValueError(
                f"{str(args)}: references unknown tag. Found {args['tag']}"
            )
        return tag


class TagSetModeEvent(TagEvent):
    def __init__(self, args: EventArgs):
        super().__init__(args)
        self.mode: str = self._parse_mode(args)
        self.transmission: List[int] = self._parse_transmission(args)

    def _parse_mode(self, args: EventArgs) -> str:
        """Parse the TagMode value from the config event's str representation

        Args:
            args (EventArgs): The config's event represenation

        Raises:
            ValueError: When an unknown mode is passed

        Returns:
            str: The parsed TagMode enum value
        """
        mode_arg: str = args.get_required_arg("mode")
        parsed_mode: TagMode | None = TagMode.from_str(mode_arg)
        if parsed_mode is None:
            raise ValueError(f"{str(args)}: has unknown mode. Found {mode_arg}")
        return parsed_mode

    def _parse_transmission(self, args: EventArgs) -> List[int]:
        """Parse the transmission from the config event's str representation.

        Args:
            args (EventArgs): The config's event represenation

        Raises:
            ValueError: When an unknown character is in the transmission

        Returns:
            List[int]: The parsed transmission as a List of 0s and 1s
        """
        transmission_arg = args.get_arg("transmission")
        if transmission_arg is None:
            return None

        transmission: List[int] = []

        # TODO: could be some binary representation,
        # but list of int works good enough since we'll probably change what the transmission event is
        for bit in transmission_arg:
            if bit == "0":
                transmission.append(0)
            elif bit == "1":
                transmission.append(1)
            else:
                raise ValueError(
                    f"{str(args)}: transmission is contains characters that are not 0 or 1. Found {transmission_arg}"
                )
        return transmission

    def run(self):
        print(f"Applying {self} to {self.tag}")
        self.tag.set_mode(self.mode)
        self.tag.set_transmission(self.transmission)
