from typing import Dict, Generator, List
from placeholder.tag import Tag
from util.identifiers import id_generator


class TagManager:
    tags: List[Tag] = list()
    named_tags: Dict[str, Tag] = dict()

    id_gen: Generator[int] = id_generator()

    @classmethod
    def register(cls, *tags: Tag) -> None:
        """Register a tag with the TagManager for any future references

        Args:
            tag (Tag): The tag to register
        """
        for tag in tags:
            id: int = next(cls.id_gen)
            tag.set_id(id)

            TagManager.named_tags[tag.name] = tag
            TagManager.tags.append(tag)

    @classmethod
    def get_by_name(cls, name: str) -> Tag:
        tag = TagManager.named_tags[name]
        assert tag is not None
        return tag

    @classmethod
    def get_by_id(cls, id: str) -> Tag:
        tag = TagManager.tags[id]
        assert tag is not None
        return tag
