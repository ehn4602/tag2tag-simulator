from typing import Dict, Generator, List
from tag import Tag
from util.identifiers import id_generator


class TagManager:
    tags: Dict[str, Tag] = dict()

    @classmethod
    def register(cls, *tags: Tag) -> None:
        """Register a tag with the TagManager for any future references

        Args:
            tag (Tag): The tag to register
        """
        for tag in tags:
            TagManager.tags[tag.name] = tag

    @classmethod
    def get_by_name(cls, name: str) -> Tag:
        tag = TagManager.named_tags[name]
        assert tag is not None
        return tag
