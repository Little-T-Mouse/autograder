
"""Original public-API A1 practice tests: DistanceMap, PriorityQueue, Truck, Fleet.

10 parameterized cases per targeted public method. No student's private
attributes or arbitrary representation choices are inspected.
Not official course tests.
"""
import random
import pytest


@pytest.mark.target_method('DistanceMap.distance')
@pytest.mark.parametrize('case', range(10))
def test_distance_lookup_cases(case):
    from distance_map import DistanceMap

    m = DistanceMap()
    assert m.distance('Unknown-A', 'Unknown-B') == -1

    cities = [
        'Depot', 'A-B', 'A', 'B-C', 'New York', 'x--y', 'École'
    ] + [
        f'City-{j:03}' for j in range(8 + case * 4)
    ]

    rng = random.Random(1000 + case)
    expected = {}

    for i, a in enumerate(cities):
        for b in cities[i + 1:]:
            ab = rng.randrange(3000)
            ba = rng.randrange(3000)

            m.add_distance(a, b, ab)
            m.add_distance(b, a, ba)

            expected[a, b] = ab
            expected[b, a] = ba

    for (a, b), value in expected.items():
        assert m.distance(a, b) == value, (a, b)

    assert m.distance('Missing', cities[0]) == -1


@pytest.mark.target_method('DistanceMap.add_distance')
@pytest.mark.parametrize('case', range(10))
def test_distance_insert_and_overwrite_cases(case):
    from distance_map import DistanceMap

    m = DistanceMap()

    pairs = [
        ('A-B', 'C'),
        ('A', 'B-C'),
        ('A-B', 'B-C'),
        ('New York', 'City 2'),
        ('x--y', 'x-y')
    ]

    for i, (a, b) in enumerate(pairs):
        d1 = case * 100 + i * 2
        d2 = d1 + 1

        m.add_distance(a, b, d1)
        assert m.distance(a, b) == d1
        assert m.distance(b, a) == d1

        m.add_distance(b, a, d2)
        assert m.distance(b, a) == d2
        assert m.distance(a, b) == d1

        m.add_distance(a, b, d1 + 50)
        assert m.distance(a, b) == d1 + 50
        assert m.distance(b, a) == d2


@pytest.mark.target_method('PriorityQueue.add')
@pytest.mark.parametrize('case', range(10))
def test_queue_add_stable_priorities(case):
    from container import PriorityQueue

    rng = random.Random(case + 200)

    values = [
        (rng.randrange(3 + case), i)
        for i in range(40 + case * 30)
    ]

    q = PriorityQueue(lambda a, b: a[0] < b[0])

    for value in values:
        q.add(value)

    assert [q.remove() for _ in values] == sorted(
        values, key=lambda x: x[0]
    )

    assert q.is_empty()


@pytest.mark.target_method('PriorityQueue.remove')
@pytest.mark.parametrize('case', range(10))
def test_queue_remove_interleaved(case):
    from container import PriorityQueue

    rng = random.Random(case + 300)
    q = PriorityQueue(lambda a, b: a[0] > b[0])
    pending = []

    for i in range(65 + case * 20):
        if not pending or rng.random() < 0.7:
            value = (rng.randrange(7 + case), i)

            q.add(value)
            pending.append(value)
        else:
            expected = sorted(
                pending, key=lambda x: -x[0]
            )[0]

            assert q.remove() == expected
            pending.remove(expected)

    for value in sorted(pending, key=lambda x: -x[0]):
        assert q.remove() == value

    assert q.is_empty()


@pytest.mark.target_method('PriorityQueue.is_empty')
@pytest.mark.parametrize('case', range(10))
def test_queue_empty_transitions(case):
    from container import PriorityQueue

    q = PriorityQueue(lambda a, b: a < b)

    assert q.is_empty() is True

    for cycle in range(1 + case):
        for n in range(cycle + 1):
            q.add(n)
            assert q.is_empty() is False

        for _ in range(cycle + 1):
            q.remove()

        assert q.is_empty() is True


def _single_truck_fleet(truck):
    from domain import Fleet

    fleet = Fleet()
    fleet.add_truck(truck)

    return fleet


@pytest.mark.target_method('Truck.pack')
@pytest.mark.parametrize('case', range(10))
def test_truck_pack_capacity_and_failures(case):
    from domain import Parcel, Truck

    capacity = [
        1, 2, 7, 10, 15, 30, 60, 100, 150, 1000
    ][case]

    truck = Truck(11, capacity, 'Depot')
    fleet = _single_truck_fleet(truck)
    rng = random.Random(case + 400)

    used = 0
    assigned = []

    if case < 4:
        volumes = [
            capacity, 1, max(1, capacity // 2)
        ]
    else:
        volumes = [
            rng.randint(1, max(2, capacity))
            for _ in range(45 + case * 10)
        ]

    for i, volume in enumerate(volumes):
        parcel = Parcel(
            i + 1, volume, 'Origin', f'City-{i % 13}'
        )

        should_fit = used + volume <= capacity

        assert truck.pack(parcel) is should_fit

        if should_fit:
            assigned.append(i + 1)
            used += volume

        # Failed packing must not change public results.
        assert fleet.parcel_allocations() == {
            11: assigned
        }

        assert truck.fullness() == pytest.approx(
            100 * used / capacity
        )


@pytest.mark.target_method('Truck.fullness')
@pytest.mark.parametrize('case', range(10))
def test_truck_fullness_cases(case):
    from domain import Parcel, Truck

    capacity = (case + 1) * 20
    truck = Truck(12, capacity, 'Depot')

    assert truck.fullness() == pytest.approx(0)

    if case % 3 == 0:
        volumes = [capacity]
    elif case % 3 == 1:
        volumes = [capacity // 4, capacity // 4]
    else:
        volumes = [
            capacity // 3, capacity // 3, capacity // 3
        ]

    used = 0

    for i, volume in enumerate(volumes):
        assert truck.pack(
            Parcel(i + 1, volume, 'Origin', f'City-{i}')
        )

        used += volume

        assert truck.fullness() == pytest.approx(
            100 * used / capacity
        )

    assert not truck.pack(
        Parcel(9000, capacity, 'Origin', 'Another')
    )

    assert truck.fullness() == pytest.approx(
        100 * used / capacity
    )


def _fleet_case(case, *, require_used=False):
    """Build a fleet using public constructors and pack()."""
    from domain import Parcel, Truck, Fleet

    rng = random.Random(case + 500)
    counts = [0, 1, 2, 3, 5, 8, 12, 16, 24, 30]
    count = counts[case]

    if require_used:
        count = max(1, count)

    fleet = Fleet()

    allocations = {}
    capacities = {}
    used = {}
    routes = {}

    destinations = [
        'A-B', 'A', 'B-C', 'New York'
    ] + [
        f'City-{i}' for i in range(18)
    ]

    for i in range(count):
        truck_id = 1000 + i * 3
        capacity = rng.randint(15, 160)

        truck = Truck(truck_id, capacity, 'Depot')

        selected = []
        volume_used = 0
        route = ['Depot']

        attempts = 1 + (i + case) % 10

        if i == 0 and require_used:
            attempts = max(1, attempts)

        if i != 0 and (i + case) % 5 == 0:
            attempts = 0

        for j in range(attempts):
            volume = rng.randint(1, 30)

            city = destinations[
                (j * 7 + i + case) % len(destinations)
            ]

            pid = 10000 + i * 100 + j
            parcel = Parcel(
                pid, volume, 'Origin', city
            )

            accepted = volume_used + volume <= capacity
            assert truck.pack(parcel) is accepted

            if accepted:
                selected.append(pid)
                volume_used += volume

                if route[-1] != city:
                    route.append(city)

        fleet.add_truck(truck)

        allocations[truck_id] = selected
        capacities[truck_id] = capacity
        used[truck_id] = volume_used
        routes[truck_id] = route

    if require_used and not any(used.values()):
        raise AssertionError(
            'Fixture must contain a used truck'
        )

    return fleet, allocations, capacities, used, routes


def _expected_distances(case, routes):
    """Create an independent directed-distance reference."""
    from distance_map import DistanceMap

    cities = [
        'Depot', 'A-B', 'A', 'B-C', 'New York'
    ] + [
        f'City-{i}' for i in range(18)
    ]

    m = DistanceMap()
    distances = {}

    for i, a in enumerate(cities):
        for j, b in enumerate(
            cities[i + 1:], start=i + 1
        ):
            forward = (
                i * 41 + j * 17 + case * 13
            ) % 199 + 1

            backward = (
                i * 11 + j * 31 + case * 7
            ) % 197 + 1

            m.add_distance(a, b, forward)
            m.add_distance(b, a, backward)

            distances[a, b] = forward
            distances[b, a] = backward

    route_total = {}

    for tid, route in routes.items():
        if len(route) > 1:
            route_total[tid] = sum(
                distances[x, y]
                for x, y in zip(route, route[1:])
            ) + distances[route[-1], 'Depot']
        else:
            route_total[tid] = 0

    return m, route_total


@pytest.mark.target_method('Fleet.add_truck')
@pytest.mark.parametrize('case', range(10))
def test_fleet_add_truck_cases(case):
    from domain import Fleet, Truck

    f = Fleet()
    assert f.num_trucks() == 0

    for i in range(1 + case * 4):
        tid = 100 + i * 2

        f.add_truck(Truck(tid, 10 + i, 'Depot'))

        assert f.num_trucks() == i + 1

    assert set(f.parcel_allocations()) == {
        100 + i * 2
        for i in range(1 + case * 4)
    }


@pytest.mark.target_method('Fleet.num_trucks')
@pytest.mark.parametrize('case', range(10))
def test_fleet_count_trucks_cases(case):
    f, allocations, _, _, _ = _fleet_case(case)

    assert f.num_trucks() == len(allocations)
    assert f.num_trucks() == len(f.trucks)


@pytest.mark.target_method('Fleet.num_nonempty_trucks')
@pytest.mark.parametrize('case', range(10))
def test_fleet_count_nonempty_cases(case):
    f, _, _, used, _ = _fleet_case(case)

    expected = sum(
        value > 0 for value in used.values()
    )

    assert f.num_nonempty_trucks() == expected


@pytest.mark.target_method('Fleet.parcel_allocations')
@pytest.mark.parametrize('case', range(10))
def test_fleet_allocations_cases(case):
    f, allocations, _, _, _ = _fleet_case(case)

    assert f.parcel_allocations() == allocations

    assert all(
        isinstance(ids, list)
        for ids in f.parcel_allocations().values()
    )


@pytest.mark.target_method('Fleet.total_unused_space')
@pytest.mark.parametrize('case', range(10))
def test_fleet_unused_space_cases(case):
    f, _, caps, used, _ = _fleet_case(case)

    expected = sum(
        caps[tid] - volume
        for tid, volume in used.items()
        if volume > 0
    )

    assert f.total_unused_space() == expected


@pytest.mark.target_method('Fleet.average_fullness')
@pytest.mark.parametrize('case', range(10))
def test_fleet_average_fullness_cases(case):
    f, _, caps, used, _ = _fleet_case(
        case, require_used=True
    )

    percentages = [
        100 * volume / caps[tid]
        for tid, volume in used.items()
        if volume > 0
    ]

    assert f.average_fullness() == pytest.approx(
        sum(percentages) / len(percentages)
    )


@pytest.mark.target_method('Fleet.total_distance_travelled')
@pytest.mark.parametrize('case', range(10))
def test_fleet_total_distance_cases(case):
    f, _, _, _, routes = _fleet_case(case)

    dmap, totals = _expected_distances(
        case, routes
    )

    assert f.total_distance_travelled(dmap) == sum(
        totals.values()
    )


@pytest.mark.target_method('Fleet.average_distance_travelled')
@pytest.mark.parametrize('case', range(10))
def test_fleet_average_distance_cases(case):
    f, _, _, used, routes = _fleet_case(
        case, require_used=True
    )

    dmap, totals = _expected_distances(
        case, routes
    )

    expected = (
        sum(totals.values()) /
        sum(v > 0 for v in used.values())
    )

    assert f.average_distance_travelled(
        dmap
    ) == pytest.approx(expected)


# Constructor checks use public effects, not private fields.

@pytest.mark.target_method('DistanceMap.__init__')
@pytest.mark.parametrize('case', range(10))
def test_distance_constructor_independent_maps(case):
    from distance_map import DistanceMap

    maps = [
        DistanceMap() for _ in range(2 + case)
    ]

    for i, m in enumerate(maps):
        assert m.distance('A-B', 'C') == -1

        m.add_distance('A-B', 'C', i + case)

        assert m.distance(
            'C', 'A-B'
        ) == i + case

    for i, m in enumerate(maps):
        assert m.distance(
            'A-B', 'C'
        ) == i + case


@pytest.mark.target_method('Parcel.__init__')
@pytest.mark.parametrize('case', range(10))
def test_parcel_constructor_observed_through_fleet(case):
    from domain import Parcel, Truck

    capacity = 10 + case * 110
    t = Truck(70, capacity, 'Depot')
    fleet = _single_truck_fleet(t)

    volumes = [
        1 + (i + case) % 7
        for i in range(1 + case * 13)
    ]

    expected = []
    used = 0

    for i, vol in enumerate(volumes):
        p = Parcel(
            500 + i, vol, 'Origin-A',
            f'City-{i % 8}'
        )

        if used + vol <= capacity:
            assert t.pack(p) is True
            used += vol
            expected.append(500 + i)
        else:
            assert t.pack(p) is False

    assert fleet.parcel_allocations() == {
        70: expected
    }

    assert t.fullness() == pytest.approx(
        100 * used / capacity
    )


@pytest.mark.target_method('Truck.__init__')
@pytest.mark.parametrize('case', range(10))
def test_truck_constructor_capacity_id_depot(case):
    from domain import Parcel, Truck
    from distance_map import DistanceMap

    depot = f'Depot-{case}'
    target = f'City-{case}'
    capacity = case * 25 + 1

    truck = Truck(900 + case, capacity, depot)
    fleet = _single_truck_fleet(truck)

    assert fleet.parcel_allocations() == {
        900 + case: []
    }

    assert truck.fullness() == pytest.approx(0)

    assert truck.pack(
        Parcel(100 + case, capacity, 'Origin', target)
    )

    assert not truck.pack(
        Parcel(200 + case, 1, 'Origin', 'Other')
    )

    assert fleet.parcel_allocations() == {
        900 + case: [100 + case]
    }

    assert truck.fullness() == pytest.approx(100)

    dmap = DistanceMap()
    dmap.add_distance(depot, target, 7 + case)
    dmap.add_distance(target, depot, 8 + case)

    assert fleet.total_distance_travelled(
        dmap
    ) == 15 + 2 * case


@pytest.mark.target_method('Fleet.__init__')
@pytest.mark.parametrize('case', range(10))
def test_fleet_constructor_empty_and_reusable(case):
    from domain import Fleet, Truck

    fleets = [
        Fleet() for _ in range(1 + case)
    ]

    for f in fleets:
        assert f.num_trucks() == 0
        assert f.num_nonempty_trucks() == 0
        assert f.parcel_allocations() == {}
        assert f.total_unused_space() == 0

    for i, f in enumerate(fleets):
        f.add_truck(
            Truck(500 + i, 10, 'Depot')
        )
        assert f.num_trucks() == 1

    assert fleets[0].num_trucks() == 1
