"""Demonstration tests. Replace or augment with your own tests for each assignment."""
import pytest
from solution import sum_positive, has_duplicates


@pytest.mark.parametrize("numbers, expected", [
    ([], 0),
    ([2, -4, 3], 5),
    ([-2, -1, 0], 0),
    ([1, 1, 1], 3),
])
def test_sum_positive(numbers, expected):
    assert sum_positive(numbers) == expected


@pytest.mark.parametrize("items, expected", [
    ([], False),
    ([1, 2, 3], False),
    ([4, 4], True),
    ([1, 2, 1], True),
])
def test_has_duplicates(items, expected):
    assert has_duplicates(items) is expected, (
        "Consider non-adjacent repeated values, not just consecutive values."
    )
