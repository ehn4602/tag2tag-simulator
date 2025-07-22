from typing import Optional, override

from event.base_event import Event
from event.event_parser import EventParser
from state import AppState
from tags.tag import Tag, TagMode


class TagEvent(Event):
    def __init__(self, parser: EventParser):
        super().__init__(parser)
        self.tag: Tag
        self._parse_tag(parser)

    def _parse_tag(self, parser: EventParser):
        tag_name: str = parser.get_required_arg("tag")

        # We need app_state to get the tag, so this is called in the prepare phase
        def set_tag(app_state: AppState):
            self.tag = parser.get_required_tag(app_state, tag_name, "tag")

        self.add_prepare_action(set_tag)


class TagSetModeEvent(TagEvent):

    def __init__(self, parser: EventParser):
        super().__init__(parser)
        self.mode: TagMode = self._parse_mode(parser)

    def _parse_mode(self, parser: EventParser) -> TagMode:
        """Parse the TagMode value from the config event's str representation

        Args:
            parser (EventParser): The config's event represenation

        Raises:
            ValueError: When an unknown mode is passed

        Returns:
            str: The parsed TagMode enum value
        """
        mode_arg: str = parser.get_required_arg("mode")
        reflection_index: Optional[int] = parser.get_arg("reflection_index")

        try:
            return TagMode.from_data(mode_arg, reflection_index)
        except ValueError as e:
            # The cause gives more details
            error_msg = f"{self}: Cannot parse mode and reflection_index."
            raise ValueError(error_msg) from e

    @override
    def run(self):
        self.tag.set_mode(self.mode)
