
"""CSC148 A1 practice tests using documented public behavior.

No private attributes or student-specific Parcel/Truck fields required.
These are independent practice tests, not official course tests.
"""

import csv
import random
import tempfile
from pathlib import Path

import pytest


# =========================================================
# TASK 1: DISTANCE MAP
# =========================================================

@pytest.mark.parametrize('a,b,d', [
    ('A-B', 'C', 12),
    ('A', 'B-C', 13),
    ('A-B', 'B-C', 14),
    ('New York', 'City-12', 27),
    ('a-b', 'A-B', 0),
    ('Toronto-West', 'Toronto-East', 19),
    ('X 1', 'X-1', 500),
    ('a--b', 'a-b', 4),
])
def test_distance_city_names(a, b, d):
    from distance_map import DistanceMap

    m = DistanceMap()
    m.add_distance(a, b, d)

    assert m.distance(a, b) == d
    assert m.distance(b, a) == d


def test_distance_keys_do_not_collide():
    from distance_map import DistanceMap

    m = DistanceMap()

    cases = [
        ('A-B', 'C', 11),
        ('A', 'B-C', 23),
        ('A-B', 'B-C', 37)
    ]

    for a, b, d in cases:
        m.add_distance(a, b, d)

    for a, b, d in cases:
        assert m.distance(a, b) == d

    assert m.distance('Unknown', 'City') == -1


@pytest.mark.parametrize('forward,backward', [
    (0, 1), (5, 10), (200, 1), (17, 17)
])
def test_distance_asymmetry_and_update(forward, backward):
    from distance_map import DistanceMap

    m = DistanceMap()

    m.add_distance('A-B', 'C', forward)
    m.add_distance('C', 'A-B', backward)

    assert m.distance('A-B', 'C') == forward
    assert m.distance('C', 'A-B') == backward

    m.add_distance('A-B', 'C', forward + 8)

    assert m.distance('A-B', 'C') == forward + 8
    assert m.distance('C', 'A-B') == backward


@pytest.mark.parametrize('seed', range(6))
def test_distance_dense_forty_city_map(seed):
    from distance_map import DistanceMap

    rng = random.Random(seed)

    cities = [
        'Depot', 'A-B', 'A', 'B-C'
    ] + [
        f'City-{i:03}' for i in range(36)
    ]

    m = DistanceMap()
    expected = {}

    for i, a in enumerate(cities):
        for b in cities[i + 1:]:
            ab = rng.randint(0, 5000)
            ba = rng.randint(0, 5000)

            m.add_distance(a, b, ab)
            m.add_distance(b, a, ba)

            expected[a, b] = ab
            expected[b, a] = ba

    for (a, b), d in expected.items():
        assert m.distance(a, b) == d, (a, b)


# =========================================================
# TASK 3: PRIORITY QUEUE
# =========================================================

@pytest.mark.parametrize('seed', range(10))
def test_priority_queue_stable_order(seed):
    from container import PriorityQueue

    rng = random.Random(seed)

    values = [
        (rng.randrange(15), i)
        for i in range(150)
    ]

    q = PriorityQueue(lambda x, y: x[0] < y[0])

    for value in values:
        q.add(value)

    expected = sorted(values, key=lambda x: x[0])
    actual = [q.remove() for _ in values]

    assert actual == expected
    assert q.is_empty()


@pytest.mark.parametrize('seed', range(10))
def test_priority_queue_interleaved_operations(seed):
    from container import PriorityQueue

    rng = random.Random(seed + 500)

    q = PriorityQueue(lambda x, y: x[0] > y[0])
    pending = []

    for idx in range(140):

        if not pending or rng.random() < 0.72:
            item = (rng.randrange(9), idx)

            pending.append(item)
            q.add(item)

        else:
            expected = sorted(
                pending,
                key=lambda x: -x[0]
            )[0]

            assert q.remove() == expected
            pending.remove(expected)

    for item in sorted(
        pending,
        key=lambda x: -x[0]
    ):
        assert q.remove() == item

    assert q.is_empty()

    q.add((8, 999))
    assert q.remove() == (8, 999)


# =========================================================
# TASK 2: TRUCK AND FLEET
# =========================================================

def _fleet_of(trucks):
    from domain import Fleet

    fleet = Fleet()

    for truck in trucks:
        fleet.add_truck(truck)

    return fleet


@pytest.mark.parametrize('capacity,volumes,expected', [
    (10, [4, 6, 1], [True, True, False]),
    (10, [9, 2, 1], [True, False, True]),
    (7, [8, 7], [False, True]),
    (1, [1, 1], [True, False]),
    (100, [20, 40, 39, 2],
     [True, True, True, False]),
])
def test_truck_pack_through_public_methods(
    capacity, volumes, expected
):
    from domain import Parcel, Truck

    truck = Truck(33, capacity, 'Depot')
    fleet = _fleet_of([truck])

    successful = []
    used = 0

    for i, (volume, should_fit) in enumerate(
        zip(volumes, expected),
        start=1
    ):
        parcel = Parcel(
            i, volume, 'Origin', f'City-{i}'
        )

        assert truck.pack(parcel) is should_fit

        if should_fit:
            successful.append(i)
            used += volume

        assert fleet.parcel_allocations() == {
            33: successful
        }

        assert truck.fullness() == pytest.approx(
            100 * used / capacity
        )

    assert fleet.num_nonempty_trucks() == int(
        bool(successful)
    )

    assert fleet.total_unused_space() == (
        capacity - used if successful else 0
    )


def test_route_return_to_depot_and_revisited_city_by_total_distance():
    from domain import Parcel, Truck
    from distance_map import DistanceMap

    t = Truck(10, 10, 'Toronto')

    # Toronto is the depot, never a parcel destination.
    destinations = ['W', 'W', 'Ottawa', 'W']

    for i, city in enumerate(destinations, start=1):
        assert t.pack(
            Parcel(i, 1, 'Origin', city)
        )

    m = DistanceMap()

    m.add_distance('Toronto', 'W', 5)
    m.add_distance('W', 'Toronto', 7)
    m.add_distance('W', 'Ottawa', 11)
    m.add_distance('Ottawa', 'W', 13)

    fleet = _fleet_of([t])

    assert fleet.parcel_allocations() == {
        10: [1, 2, 3, 4]
    }

    # Toronto -> W -> Ottawa -> W -> Toronto
    # Consecutive duplicate W is not another stop.
    assert fleet.total_distance_travelled(m) == (
        5 + 11 + 13 + 7
    )

    assert fleet.average_distance_travelled(
        m
    ) == pytest.approx(36)


@pytest.mark.parametrize('seed', range(10))
def test_fleet_many_trucks_using_public_methods(seed):
    from domain import Parcel, Truck

    rng = random.Random(seed)

    trucks = []
    expected = {}
    full_percentages = []
    unused = 0

    for j in range(15):
        capacity = rng.randint(25, 100)
        truck = Truck(100 + j, capacity, 'Depot')

        remaining = capacity
        assigned = []

        for k in range(rng.randrange(7)):
            v = rng.randint(1, 30)
            pid = j * 100 + k

            accepted = v <= remaining

            assert truck.pack(
                Parcel(
                    pid, v, 'Origin', f'City-{k}'
                )
            ) is accepted

            if accepted:
                remaining -= v
                assigned.append(pid)

        expected[100 + j] = assigned

        if assigned:
            unused += remaining

            full_percentages.append(
                100 * (capacity - remaining) / capacity
            )

        trucks.append(truck)

    fleet = _fleet_of(trucks)

    assert fleet.num_trucks() == len(trucks)

    assert fleet.parcel_allocations() == expected

    assert fleet.num_nonempty_trucks() == len(
        full_percentages
    )

    assert fleet.total_unused_space() == unused

    if full_percentages:
        assert fleet.average_fullness() == pytest.approx(
            sum(full_percentages) / len(full_percentages)
        )


# =========================================================
# TASKS 4 AND 5: GREEDY, RANDOM AND EXPERIMENT
# =========================================================

def _fixture_files(
    experiment, parcels, trucks, cities, rng
):
    """Create temporary CSV files beside experiment.py."""

    root = Path(experiment.__file__).resolve().parent

    temp = tempfile.TemporaryDirectory(
        prefix='a1_public_',
        dir=root
    )

    relative = Path(temp.name).name

    paths = {
        'parcel_file': f'{relative}/parcels.csv',
        'truck_file': f'{relative}/trucks.csv',
        'map_file': f'{relative}/map.csv',
    }

    with (
        root / paths['parcel_file']
    ).open('w', newline='', encoding='utf8') as f:
        csv.writer(f).writerows(parcels)

    with (
        root / paths['truck_file']
    ).open('w', newline='', encoding='utf8') as f:
        csv.writer(f).writerows(trucks)

    with (
        root / paths['map_file']
    ).open('w', newline='', encoding='utf8') as f:
        w = csv.writer(f)

        for i, a in enumerate(cities):
            for b in cities[i + 1:]:
                w.writerow((
                    a,
                    b,
                    rng.randint(1, 500),
                    rng.randint(1, 500)
                ))

    return temp, paths, root


def _data(seed, count):
    rng = random.Random(seed)

    cities = [
        'Depot', 'A-B', 'A', 'B-C'
    ] + [
        f'City-{i:02}' for i in range(21)
    ]

    parcels = [
        (
            i + 1,
            'Origin',
            rng.choice(cities[1:]),
            rng.randint(1, 19)
        )
        for i in range(count)
    ]

    trucks = [
        (
            100 + i,
            250 if i == 0 else rng.randint(30, 90)
        )
        for i in range(12)
    ]

    return parcels, trucks, cities, rng


def _reference_greedy(parcels, trucks, options):
    """Calculate expected greedy allocations independently."""

    if options[0] == 'volume':
        key = lambda p: p[3]
    else:
        key = lambda p: p[2]

    ordered = sorted(
        parcels,
        key=key,
        reverse=options[1] == 'non-increasing'
    )

    used = [0] * len(trucks)
    last = ['Depot'] * len(trucks)

    allocations = {
        truck_id: []
        for truck_id, _ in trucks
    }

    failed = 0

    for pid, source, dest, volume in ordered:

        eligible = [
            i
            for i, (_, capacity) in enumerate(trucks)
            if capacity - used[i] >= volume
        ]

        if not eligible:
            failed += 1
            continue

        matching = [
            i
            for i in eligible
            if last[i] == dest
        ]

        if matching:
            eligible = matching

        if options[2] == 'non-decreasing':
            chosen = min(
                eligible,
                key=lambda i: trucks[i][1] - used[i]
            )
        else:
            chosen = max(
                eligible,
                key=lambda i: trucks[i][1] - used[i]
            )

        used[chosen] += volume
        last[chosen] = dest

        allocations[trucks[chosen][0]].append(pid)

    return allocations, failed


@pytest.mark.parametrize(
    'priority',
    ['volume', 'destination']
)
@pytest.mark.parametrize(
    'parcel_order',
    ['non-decreasing', 'non-increasing']
)
@pytest.mark.parametrize(
    'truck_order',
    ['non-decreasing', 'non-increasing']
)
@pytest.mark.parametrize('seed', range(3))
def test_greedy_all_eight_modes_via_public_experiment_api(
    seed, priority, parcel_order, truck_order, monkeypatch
):
    import experiment

    parcels, trucks, cities, rng = _data(seed, 65)

    options = (
        priority, parcel_order, truck_order
    )

    expected, failed = _reference_greedy(
        parcels, trucks, options
    )

    temp, paths, root = _fixture_files(
        experiment, parcels, trucks, cities, rng
    )

    try:
        monkeypatch.chdir(root)

        config = dict(
            paths,
            depot_location='Depot',
            algorithm='greedy',
            parcel_priority=priority,
            parcel_order=parcel_order,
            truck_order=truck_order
        )

        e = experiment.SchedulingExperiment(config)
        stats = e.run()

        # The experiment's fleet attribute is public.
        # parcel_allocations() is a documented public method.
        assert e.fleet.parcel_allocations() == expected

        assert stats['unscheduled'] == failed
        assert stats['fleet'] == len(trucks)

        assert stats['unused_trucks'] == sum(
            not ids for ids in expected.values()
        )

    finally:
        temp.cleanup()


@pytest.mark.parametrize('seed', range(8))
def test_random_scheduling_public_invariants(
    seed, monkeypatch
):
    import experiment

    parcels, trucks, cities, rng = _data(
        seed + 1000, 90
    )

    temp, paths, root = _fixture_files(
        experiment, parcels, trucks, cities, rng
    )

    try:
        monkeypatch.chdir(root)

        config = dict(
            paths,
            depot_location='Depot',
            algorithm='random',
            parcel_priority='volume',
            parcel_order='non-decreasing',
            truck_order='non-decreasing'
        )

        e = experiment.SchedulingExperiment(config)
        result = e.run()

        allocations = e.fleet.parcel_allocations()

        assigned = [
            pid
            for ids in allocations.values()
            for pid in ids
        ]

        original_ids = {
            p[0] for p in parcels
        }

        assert len(assigned) == len(set(assigned))

        assert set(assigned) <= original_ids

        assert (
            len(assigned) + result['unscheduled']
            == len(parcels)
        )

        assert result['fleet'] == len(trucks)

        assert result['unused_trucks'] == sum(
            not ids for ids in allocations.values()
        )

        assert 0 <= result['avg_fullness'] <= 100

    finally:
        temp.cleanup()
