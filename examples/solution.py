"""Example student code for the demo assignment. The second function has a bug."""


def sum_positive(numbers: list[int]) -> int:
    """Return the sum of all strictly positive numbers in numbers."""
    return sum(n for n in numbers if n > 0)


def has_duplicates(items: list) -> bool:
    """Return whether items contains the same value at least twice."""
    # Deliberate bug: this only compares the first two items.
    return len(items) > 1 and items[0] == items[1]
