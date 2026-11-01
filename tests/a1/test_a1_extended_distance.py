
"""Independent A1 practice tests: unusual city strings and dense distance maps.

All values are generated in this file; no course-provided tests or data are used.
"""

import random

import pytest


@pytest.mark.parametrize('source,destination,distance', [
    ('A-B', 'C', 8), ('A', 'B-C', 13), ('A-B', 'B-C', 4),
    ('Toronto-West', 'Toronto-East', 9), ('New York', 'Los Angeles', 7),
    ('x1', 'y2', 0), ('A B', 'A-B', 24), ('école', 'Montréal', 11),
    ('City 005', 'City 050', 900), ('abc', 'ABC', 17),
    ('A--B', 'A-B', 2), ('A-B-C', 'D', 3), ('A', 'B-C-D', 5),
    ('North/West', 'North/East', 21), ('x.y', 'x-y', 1),
])
def test_city_name_is_preserved_exactly(source, destination, distance):
    from distance_map import DistanceMap
    m = DistanceMap()
    m.add_distance(source, destination, distance)
    assert m.distance(source, destination) == distance
    assert m.distance(destination, source) == distance


def test_hyphenated_names_cannot_collide():
    from distance_map import DistanceMap
    m = DistanceMap()
    cases = [('A-B', 'C', 11), ('A', 'B-C', 23),
             ('A-B', 'B-C', 37), ('A-B-C', 'D', 42)]
    for source, destination, distance in cases:
        m.add_distance(source, destination, distance)
    for source, destination, distance in cases:
        assert m.distance(source, destination) == distance


@pytest.mark.parametrize('forward,backward', [(0, 0), (1, 2), (2, 1),
                                               (20, 80), (100, 0), (0, 100)])
def test_asymmetric_reverse_then_forward_update(forward, backward):
    from distance_map import DistanceMap
    m = DistanceMap()
    m.add_distance('South', 'North', forward)
    m.add_distance('North', 'South', backward)
    assert m.distance('South', 'North') == forward
    assert m.distance('North', 'South') == backward
    m.add_distance('South', 'North', forward + 100)
    assert m.distance('South', 'North') == forward + 100
    assert m.distance('North', 'South') == backward


@pytest.mark.parametrize('seed', range(8))
def test_dense_map_of_40_cities(seed):
    from distance_map import DistanceMap
    rng = random.Random(seed)
    cities = ['Depot', 'A-B', 'A', 'B-C'] + [f'City-{i:03}' for i in range(36)]
    expected = {}
    m = DistanceMap()
    for i, source in enumerate(cities):
        for destination in cities[i + 1:]:
            forward = rng.randint(0, 50000)
            backward = rng.randint(0, 50000)
            m.add_distance(source, destination, forward)
            m.add_distance(destination, source, backward)
            expected[(source, destination)] = forward
            expected[(destination, source)] = backward
    for (source, destination), distance in expected.items():
        assert m.distance(source, destination) == distance, (source, destination)
