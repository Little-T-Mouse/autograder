
"""Independent A1 practice tests for Parcel, Truck and Fleet public methods."""

import random

import pytest


@pytest.mark.parametrize('capacity,volumes,accepted', [
    (1, [1, 1], [True, False]),
    (10, [4, 6, 1], [True, True, False]),
    (10, [9, 2, 1], [True, False, True]),
    (15, [4, 5, 6], [True, True, True]),
    (100, [20, 40, 39, 2], [True, True, True, False]),
    (7, [8, 7], [False, True]),
    (20, [5, 11, 5], [True, True, False]),
    (33, [11, 11, 11, 1], [True, True, True, False]),
])
def test_pack_boundary_and_no_mutation_on_failure(capacity, volumes, accepted):
    from domain import Parcel, Truck
    truck = Truck(5, capacity, 'Depot')
    expected_used = 0
    destinations = []
    packed_ids = []
    for i, (volume, should_fit) in enumerate(zip(volumes, accepted)):
        parcel = Parcel(i + 1, volume, 'Origin-X', f'City-{i}')
        old = (truck.used_space, truck.route[:], truck.parcel[:])
        assert truck.pack(parcel) is should_fit
        if should_fit:
            expected_used += volume
            packed_ids.append(parcel.id_)
            destinations.append(parcel.destination)
        else:
            assert (truck.used_space, truck.route, truck.parcel) == old
    assert truck.used_space == expected_used
    assert [p.id_ for p in truck.parcel] == packed_ids
    assert truck.route == ['Depot'] + destinations
    assert truck.fullness() == pytest.approx(expected_used / capacity * 100)


@pytest.mark.parametrize('names', [
    ['A-B', 'A-B', 'B-C'],
    ['A', 'B', 'A', 'A'],
    ['W', 'X', 'W', 'Y'],
    ['X', 'X', 'X', 'X'],
    ['City-3', 'City-2', 'City-3'],
])
def test_route_deduplicates_only_consecutive_destinations(names):
    from domain import Parcel, Truck
    t = Truck(7, 100, 'Depot')
    expected = ['Depot']
    for i, name in enumerate(names):
        assert t.pack(Parcel(i, 1, 'Source', name))
        if expected[-1] != name:
            expected.append(name)
    assert t.route == expected
    assert len(t.parcel) == len(names)


@pytest.mark.parametrize('seed', range(10))
def test_fleet_statistics_against_independent_calculation(seed):
    from domain import Parcel, Truck, Fleet
    rng = random.Random(seed)
    fleet = Fleet()
    expected_allocations = {}
    used_fullness = []
    unused_space = 0
    for truck_index in range(12):
        capacity = rng.randint(25, 100)
        t = Truck(100 + truck_index, capacity, 'Depot')
        remaining = capacity
        ids = []
        for parcel_index in range(rng.randint(0, 6)):
            volume = rng.randint(1, 30)
            p = Parcel(truck_index * 100 + parcel_index, volume,
                       'Origin', f'City-{parcel_index}')
            if volume <= remaining:
                assert t.pack(p)
                remaining -= volume
                ids.append(p.id_)
            else:
                assert not t.pack(p)
        expected_allocations[t.id_] = ids
        if ids:
            used_fullness.append((capacity - remaining) / capacity * 100)
            unused_space += remaining
        fleet.add_truck(t)
    assert fleet.num_trucks() == 12
    assert fleet.num_nonempty_trucks() == len(used_fullness)
    assert fleet.parcel_allocations() == expected_allocations
    assert fleet.total_unused_space() == unused_space
    if used_fullness:
        assert fleet.average_fullness() == pytest.approx(
            sum(used_fullness) / len(used_fullness))


@pytest.mark.parametrize('seed', range(6))
def test_multi_city_fleet_round_trip_distance(seed):
    from domain import Parcel, Truck, Fleet
    from distance_map import DistanceMap
    rng = random.Random(seed)
    cities = ['Depot', 'A-B', 'A', 'B-C'] + [f'City-{i}' for i in range(12)]
    m = DistanceMap()
    expected_map = {}
    for i, a in enumerate(cities):
        for b in cities[i + 1:]:
            forward, backward = rng.randint(1, 200), rng.randint(1, 200)
            m.add_distance(a, b, forward)
            m.add_distance(b, a, backward)
            expected_map[a, b] = forward
            expected_map[b, a] = backward
    fleet = Fleet()
    expected_distances = []
    for t_id in range(8):
        truck = Truck(t_id, 100, 'Depot')
        route = ['Depot']
        for p_id in range(rng.randint(0, 7)):
            city = rng.choice(cities[1:])
            assert truck.pack(Parcel(t_id * 100 + p_id, 1, 'Origin', city))
            if route[-1] != city:
                route.append(city)
        fleet.add_truck(truck)
        if truck.parcel:
            expected_distances.append(sum(
                expected_map[route[i], route[i + 1]]
                for i in range(len(route) - 1)
            ) + expected_map[route[-1], 'Depot'])
    assert fleet.total_distance_travelled(m) == sum(expected_distances)
    if expected_distances:
        assert fleet.average_distance_travelled(m) == pytest.approx(
            sum(expected_distances) / len(expected_distances))
