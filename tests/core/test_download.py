from types import SimpleNamespace

from aw_cli import download


def response(status_code: int, content_range: str = ""):
    return SimpleNamespace(
        status_code=status_code,
        headers={"content-range": content_range} if content_range else {},
    )


def test_segment_ranges_cover_file_without_gaps():
    assert download._segment_ranges(total=10, connections=3) == [
        (0, 3),
        (4, 6),
        (7, 9),
    ]


def test_segment_ranges_do_not_create_empty_ranges():
    assert download._segment_ranges(total=3, connections=10) == [
        (0, 0),
        (1, 1),
        (2, 2),
    ]


def test_valid_partial_response_accepts_matching_content_range():
    assert download._valid_partial_response(
        response(206, "bytes 4-6/10"),
        start=4,
        end=6,
        total=10,
    )


def test_valid_partial_response_rejects_ignored_range():
    assert not download._valid_partial_response(
        response(200, "bytes 0-9/10"),
        start=4,
        end=6,
        total=10,
    )


def test_valid_partial_response_rejects_wrong_content_range():
    assert not download._valid_partial_response(
        response(206, "bytes 0-6/10"),
        start=4,
        end=6,
        total=10,
    )
