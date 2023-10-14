from typing import Iterable, Literal, TYPE_CHECKING, TypeAlias, reveal_type

WebtoonId: TypeAlias = 'int | tuple[int, int] | tuple[str, int] | str'  # + ' | NaverPostWebtoonId | NaverBlogWebtoonId'
EpisodeNoRange: TypeAlias = 'tuple[int | None, int | None] | int | None'
