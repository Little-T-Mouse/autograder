"""Independent, student-facing A1 practice cases. Not course-provided tests."""
import pytest


def test_map_unknown_city_pair_gives_sentinel():
    from distance_map import DistanceMap
    atlas = DistanceMap()
    assert atlas.distance('Cedar', 'Birch') == -1


def test_map_insertion_supports_return_trip():
    from distance_map import DistanceMap
    atlas = DistanceMap()
    atlas.add_distance('Cedar', 'Birch', 19)
    assert atlas.distance('Cedar', 'Birch') == 19
    assert atlas.distance('Birch', 'Cedar') == 19


def test_map_distinct_forward_and_backward_distances():
    from distance_map import DistanceMap
    atlas = DistanceMap()
    atlas.add_distance('Birch', 'Elm', 21)
    atlas.add_distance('Elm', 'Birch', 33)
    assert atlas.distance('Birch', 'Elm') == 21
    assert atlas.distance('Elm', 'Birch') == 33


def test_map_replacing_one_direction_preserves_the_other():
    from distance_map import DistanceMap
    atlas = DistanceMap()
    atlas.add_distance('Bay', 'Hill', 9)
    atlas.add_distance('Hill', 'Bay', 10)
    atlas.add_distance('Bay', 'Hill', 12)
    assert (atlas.distance('Bay', 'Hill'), atlas.distance('Hill', 'Bay')) == (12, 10)


def test_queue_removes_smallest_priority_first():
    from container import PriorityQueue
    queue = PriorityQueue(lambda x, y: x < y)
    for number in [11, 4, 15, 1, 8]:
        queue.add(number)
    assert [queue.remove() for _ in range(5)] == [1, 4, 8, 11, 15]
    assert queue.is_empty()


def test_queue_supports_reverse_comparison():
    from container import PriorityQueue
    queue = PriorityQueue(lambda x, y: x > y)
    for number in [6, 6, 4, 9]:
        queue.add(number)
    assert [queue.remove() for _ in range(4)] == [9, 6, 6, 4]


def test_queue_equal_priorities_keep_original_order():
    from container import PriorityQueue
    queue = PriorityQueue(lambda x, y: x[0] < y[0])
    for pair in [(2, 'first'), (1, 'early'), (2, 'second'), (2, 'third')]:
        queue.add(pair)
    assert [queue.remove()[1] for _ in range(4)] == [
        'early', 'first', 'second', 'third'
    ]


def test_queue_works_after_becoming_empty():
    from container import PriorityQueue
    queue = PriorityQueue(lambda x, y: x < y)
    queue.add(8)
    assert queue.remove() == 8
    assert queue.is_empty()
    queue.add(5)
    queue.add(3)
    assert queue.remove() == 3
    assert queue.remove() == 5
