
"""Independent A1 practice tests: priority, FIFO ties and repeated operations."""

import random

import pytest


@pytest.mark.parametrize('seed', range(10))
def test_queue_matches_stable_integer_reference(seed):
    from container import PriorityQueue
    rng = random.Random(seed)
    values = [rng.randint(-20, 20) for _ in range(220)]
    # Items have an insertion ID so FIFO behavior is independently observable.
    items = [(value, index) for index, value in enumerate(values)]
    q = PriorityQueue(lambda a, b: a[0] < b[0])
    for item in items:
        q.add(item)
    assert [q.remove() for _ in items] == sorted(items, key=lambda x: x[0])
    assert q.is_empty()


@pytest.mark.parametrize('seed', range(10))
def test_queue_handles_interleaved_operations(seed):
    from container import PriorityQueue
    rng = random.Random(seed + 900)
    q = PriorityQueue(lambda a, b: a[0] > b[0])
    pending = []
    index = 0
    for _ in range(180):
        if not pending or rng.random() < 0.7:
            item = (rng.randint(1, 10), index)
            index += 1
            q.add(item)
            pending.append(item)
        else:
            expected = sorted(pending, key=lambda x: -x[0])[0]
            assert q.remove() == expected
            pending.remove(expected)
    for item in sorted(pending, key=lambda x: -x[0]):
        assert q.remove() == item
    assert q.is_empty()


@pytest.mark.parametrize('words', [
    ['aaa', 'bbb', 'c', 'd', 'zzzz'],
    ['x', 'y', 'z', 'ab', 'cd'],
    ['A-B', 'X-Y', 'Longer', 'Z'],
    ['one', 'two', 'six', 'ten', 'four'],
])
def test_equal_string_length_keeps_fifo_order(words):
    from container import PriorityQueue
    q = PriorityQueue(lambda a, b: len(a) < len(b))
    for word in words:
        q.add(word)
    assert [q.remove() for _ in words] == sorted(words, key=len)


def test_queue_can_be_reused_after_becoming_empty():
    from container import PriorityQueue
    q = PriorityQueue(lambda a, b: a < b)
    for cycle in range(12):
        assert q.is_empty()
        for n in (cycle + 3, cycle + 1, cycle + 2):
            q.add(n)
        assert [q.remove() for _ in range(3)] == [cycle + 1, cycle + 2, cycle + 3]
