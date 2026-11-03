import time

from app.db import new_uuid7


def test_generates_version_7_uuids() -> None:
    assert new_uuid7().version == 7


def test_later_ids_sort_after_earlier_ones() -> None:
    first = new_uuid7()
    time.sleep(0.005)
    second = new_uuid7()

    assert first < second
