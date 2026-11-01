
"""Independent A1 practice tests: deterministic greedy oracle and random invariants.

Test data is generated with fixed seeds. Expected greedy allocations are
calculated by a separate, plain-list model, not by another student module.
"""

import random

import pytest


OPTIONS = [(priority, parcel_order, truck_order)
           for priority in ('volume', 'destination')
           for parcel_order in ('non-decreasing', 'non-increasing')
           for truck_order in ('non-decreasing', 'non-increasing')]


def _scenario(seed, count):
    rng = random.Random(seed * 1009 + count)
    cities = ['A-B', 'A', 'B-C', 'City-4', 'City 5'] + [
        f'Municipality-{i:02}' for i in range(17)
    ]
    parcels = [(i + 1, rng.randint(1, 18), 'Origin', rng.choice(cities))
               for i in range(count)]
    trucks = [(100 + i, rng.randint(20, 85)) for i in range(12)]
    return parcels, trucks


def _expected_greedy(parcels, trucks, options):
    """Plain Python behavioral reference for the documented greedy policy."""
    priority, parcel_order, truck_order = options
    key = (lambda p: p[1]) if priority == 'volume' else (lambda p: p[3])
    ordered = sorted(parcels, key=key,
                     reverse=(parcel_order == 'non-increasing'))
    remaining = [capacity for _, capacity in trucks]
    end_city = ['Depot' for _ in trucks]
    allocations = [[] for _ in trucks]
    unscheduled = []
    for parcel in ordered:
        p_id, volume, _, destination = parcel
        eligible = [i for i, space in enumerate(remaining) if space >= volume]
        if not eligible:
            unscheduled.append(p_id)
            continue
        matching = [i for i in eligible if end_city[i] == destination]
        if matching:
            eligible = matching
        if truck_order == 'non-decreasing':
            best = min(eligible, key=lambda i: remaining[i])
        else:
            best = max(eligible, key=lambda i: remaining[i])
        remaining[best] -= volume
        allocations[best].append(p_id)
        end_city[best] = destination
    return allocations, remaining, unscheduled


@pytest.mark.parametrize('options', OPTIONS)
@pytest.mark.parametrize('seed', range(6))
@pytest.mark.parametrize('count', (15, 75))
def test_greedy_matches_independent_reference(options, seed, count):
    from domain import Parcel, Truck
    from scheduler import GreedyScheduler

    data, capacities = _scenario(seed, count)
    parcels = [Parcel(*record) for record in data]
    trucks = [Truck(t_id, capacity, 'Depot') for t_id, capacity in capacities]
    parcel_snapshot = [(p.id_, p.volume, p.source, p.destination) for p in parcels]
    original_parcels = parcels[:]
    original_trucks = trucks[:]
    config = dict(zip(('parcel_priority', 'parcel_order', 'truck_order'), options))

    allocations, remaining, not_scheduled = _expected_greedy(
        data, capacities, options)
    leftovers = GreedyScheduler(config).schedule(parcels, trucks)

    assert [[p.id_ for p in t.parcel] for t in trucks] == allocations
    assert [t.capacity - t.used_space for t in trucks] == remaining
    assert [p.id_ for p in leftovers] == not_scheduled
    assert parcels == original_parcels
    assert trucks == original_trucks
    assert [(p.id_, p.volume, p.source, p.destination) for p in parcels] == parcel_snapshot
    # No parcel is lost or assigned to more than one truck.
    all_ids = [p.id_ for t in trucks for p in t.parcel] + [p.id_ for p in leftovers]
    assert sorted(all_ids) == sorted(p.id_ for p in parcels)


@pytest.mark.parametrize('seed', range(8))
@pytest.mark.parametrize('count', (15, 75))
def test_random_scheduler_preserves_inputs_and_capacity(seed, count):
    from domain import Parcel, Truck
    from scheduler import RandomScheduler

    data, capacities = _scenario(seed, count)
    parcels = [Parcel(*record) for record in data]
    trucks = [Truck(t_id, capacity, 'Depot') for t_id, capacity in capacities]
    original_parcels, original_trucks = parcels[:], trucks[:]
    snapshots = [(p.id_, p.volume, p.source, p.destination) for p in parcels]
    old_random_state = random.getstate()
    try:
        random.seed(seed)
        leftovers = RandomScheduler().schedule(parcels, trucks)
    finally:
        random.setstate(old_random_state)

    assert parcels == original_parcels
    assert trucks == original_trucks
    assert [(p.id_, p.volume, p.source, p.destination) for p in parcels] == snapshots
    all_parcels = [p for t in trucks for p in t.parcel] + leftovers
    assert sorted(p.id_ for p in all_parcels) == sorted(p.id_ for p in parcels)
    for t in trucks:
        assert 0 <= t.used_space <= t.capacity
        assert t.used_space == sum(p.volume for p in t.parcel)
        assert t.route[0] == 'Depot'
        expected_route = ['Depot']
        for p in t.parcel:
            if expected_route[-1] != p.destination:
                expected_route.append(p.destination)
        assert t.route == expected_route
    # If a parcel failed to fit at its turn, adding more parcels cannot make it fit later.
    assert all(all(t.capacity - t.used_space < p.volume for t in trucks)
               for p in leftovers)


def test_random_empty_parcel_list_leaves_trucks_unchanged():
    from domain import Truck
    from scheduler import RandomScheduler
    trucks = [Truck(1, 5, 'Depot'), Truck(2, 10, 'Depot')]
    assert RandomScheduler().schedule([], trucks) == []
    assert [t.route for t in trucks] == [['Depot'], ['Depot']]


def test_greedy_already_at_destination_takes_precedence_over_more_space():
    from domain import Parcel, Truck
    from scheduler import GreedyScheduler
    small, large = Truck(1, 8, 'Depot'), Truck(2, 90, 'Depot')
    assert small.pack(Parcel(999, 2, 'Depot', 'A-B'))
    next_parcel = Parcel(1, 3, 'Depot', 'A-B')
    config = {'parcel_priority': 'volume', 'parcel_order': 'non-decreasing',
              'truck_order': 'non-increasing'}
    assert GreedyScheduler(config).schedule([next_parcel], [small, large]) == []
    assert small.parcel[-1] is next_parcel
    assert large.parcel == []
