import pytest
from WebtoonScraper.scrapers import EpisodeRange


def test_episode_range():
    e = EpisodeRange()
    for r in (slice(None, 2, None), slice(10, 18, 2), {6, 7}, 3, 4):
        e.add(r)
    assert [i for i in range(20) if i in e] == [1, 3, 4, 6, 7, 10, 12, 14, 16]

    e = EpisodeRange.from_string("~1,3,4,6,10~18,7", inclusive=True)
    assert [i for i in range(20) if i in e] == [1, 3, 4, 6, 7, 10, 11, 12, 13, 14, 15, 16, 17, 18]

    # 역방향 range는 무시됨
    e = EpisodeRange.from_string("~1,3,4,6,18~10,7", inclusive=True)
    assert [i for i in range(20) if i in e] == [1, 3, 4, 6, 7]

    e = EpisodeRange.from_string("~1,3,4,6,10~,7", inclusive=True)
    assert [i for i in range(20) if i in e] == [1, 3, 4, 6, 7, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]

    with pytest.raises(ValueError):
        EpisodeRange.from_string("~1,3,4,6,hi~,7", inclusive=True)

    with pytest.raises(ValueError):
        EpisodeRange.from_string("~1,3,4,6,hi~,7", inclusive=True)

    e = EpisodeRange.from_string("~1,3,4,6,10~,7,!15", inclusive=True)
    assert [i for i in range(20) if i in e] == [1, 3, 4, 6, 7, 10, 11, 12, 13, 14, 16, 17, 18, 19]

    e = EpisodeRange.from_string("~1,3,4,6,10~,7,!12~18,16", inclusive=True)
    assert [i for i in range(20) if i in e] == [1, 3, 4, 6, 7, 10, 11, 16, 19]
