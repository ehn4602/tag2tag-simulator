from typing import Dict

from tags.tag import Tag


class TagManager:
    tags: Dict[str, Tag] = dict()

    def register(cls, *tags: Tag) -> None:
        """Register a tag with the TagManager for any future references

        Args:
            tag (Tag): The tag to register
        """
        for tag in tags:
            TagManager.tags[tag.name] = tag

    def get_by_name(cls, name: str) -> Tag:
        tag = TagManager.tags[name]
        assert tag is not None
        return tag
