
"""Original A1 practice tests: readers, scheduling and experiments.

10 parameterized cases per public target method.
Creates synthetic CSV files and many-city networks.
Never examines student-defined private fields.
"""

import contextlib
import csv
import random
import tempfile
from pathlib import Path

import pytest


def _scenario(case, count=None):
    rng = random.Random(8000 + case)

    cities = [
        'Depot', 'A-B', 'A', 'B-C',
        'New York', 'X--Y'
    ] + [
        f'Municipality-{j:02}'
        for j in range(5 + case * 3)
    ]

    n = count if count is not None else 10 + case * 14

    parcels = [
        (
            j + 1,
            'Origin',
            rng.choice(cities[1:]),
            rng.randint(1, 30)
        )
        for j in range(n)
    ]

    trucks = [
        (
            1000 + j,
            400 if j == 0 else rng.randint(24, 125)
        )
        for j in range(2 + case * 2)
    ]

    distances = {}
    rows = []

    for i, a in enumerate(cities):
        for j, b in enumerate(
            cities[i + 1:], start=i + 1
        ):
            ab = rng.randint(1, 1500)
            ba = rng.randint(1, 1500)

            rows.append((a, b, ab, ba))

            distances[a, b] = ab
            distances[b, a] = ba

    return parcels, trucks, rows, distances, cities


@contextlib.contextmanager
def _files(experiment, parcels, trucks, distances):
    """Create valid temporary CSV files beside experiment.py."""

    root = Path(experiment.__file__).resolve().parent

    with tempfile.TemporaryDirectory(
        prefix='a1_practice_',
        dir=root
    ) as directory:

        relative = Path(directory).name

        data = {
            'parcel_file': f'{relative}/parcels.csv',
            'truck_file': f'{relative}/trucks.csv',
            'map_file': f'{relative}/map.csv'
        }

        for path, rows in [
            (data['parcel_file'], parcels),
            (data['truck_file'], trucks),
            (data['map_file'], distances)
        ]:
            with (
                root / path
            ).open('w', encoding='utf8', newline='') as out:
                csv.writer(out).writerows(rows)

        yield data, root


def _config(
    files,
    options=(
        'volume',
        'non-decreasing',
        'non-decreasing'
    ),
    algorithm='greedy'
):
    return {
        **files,
        'depot_location': 'Depot',
        'algorithm': algorithm,
        'parcel_priority': options[0],
        'parcel_order': options[1],
        'truck_order': options[2]
    }


def _greedy_expected(parcels, trucks, distances, options):
    """Independent deterministic list-based greedy reference."""

    if options[0] == 'volume':
        key = lambda p: p[3]
    else:
        key = lambda p: p[2]

    ordered = sorted(
        parcels,
        key=key,
        reverse=options[1] == 'non-increasing'
    )

    remaining = [
        capacity for _, capacity in trucks
    ]

    routes = [
        ['Depot'] for _ in trucks
    ]

    allocations = {
        tid: [] for tid, _ in trucks
    }

    unscheduled = []

    for pid, _, destination, volume in ordered:

        eligible = [
            i for i in range(len(trucks))
            if remaining[i] >= volume
        ]

        if not eligible:
            unscheduled.append(pid)
            continue

        same = [
            i for i in eligible
            if routes[i][-1] == destination
        ]

        if same:
            eligible = same

        if options[2] == 'non-decreasing':
            best = min(
                eligible,
                key=lambda i: remaining[i]
            )
        else:
            best = max(
                eligible,
                key=lambda i: remaining[i]
            )

        remaining[best] -= volume

        allocations[
            trucks[best][0]
        ].append(pid)

        if routes[best][-1] != destination:
            routes[best].append(destination)

    used_indices = [
        i for i in range(len(trucks))
        if allocations[trucks[i][0]]
    ]

    used_fullness = [
        100 * (
            trucks[i][1] - remaining[i]
        ) / trucks[i][1]
        for i in used_indices
    ]

    total_distance = sum(
        sum(
            distances[a, b]
            for a, b in zip(
                routes[i], routes[i][1:]
            )
        ) + distances[
            routes[i][-1], 'Depot'
        ]
        for i in used_indices
    )

    stats = {
        'fleet': len(trucks),
        'unused_trucks': (
            len(trucks) - len(used_indices)
        ),
        'unused_space': sum(
            remaining[i] for i in used_indices
        ),
        'unscheduled': len(unscheduled),
        'avg_fullness': (
            sum(used_fullness) / len(used_indices)
        ),
        'avg_distance': (
            total_distance / len(used_indices)
        )
    }

    return allocations, unscheduled, stats


# =========================================================
# READ PARCELS
# =========================================================

@pytest.mark.target_method('read_parcels')
@pytest.mark.parametrize('case', range(10))
def test_reader_parcels_10_scenarios(
    case, monkeypatch
):
    import experiment
    from domain import Truck, Fleet, Parcel

    parcels, trucks, rows, _, _ = _scenario(
        case, 1 + 25 * case
    )

    with _files(
        experiment, parcels, trucks, rows
    ) as (paths, root):

        monkeypatch.chdir(root)

        result = experiment.read_parcels(
            paths['parcel_file']
        )

        assert len(result) == len(parcels)
        assert all(
            isinstance(p, Parcel)
            for p in result
        )

        total_volume = sum(
            row[3] for row in parcels
        )

        truck = Truck(
            88, total_volume + 1, 'Depot'
        )

        for p in result:
            assert truck.pack(p) is True

        fleet = Fleet()
        fleet.add_truck(truck)

        assert fleet.parcel_allocations() == {
            88: [row[0] for row in parcels]
        }

        assert truck.fullness() == pytest.approx(
            total_volume * 100 /
            (total_volume + 1)
        )


# =========================================================
# READ DISTANCE MAP
# =========================================================

@pytest.mark.target_method('read_distance_map')
@pytest.mark.parametrize('case', range(10))
def test_reader_distances_10_scenarios(
    case, monkeypatch
):
    import experiment

    parcels, trucks, rows, _, _ = _scenario(case)

    mixed_rows = []
    expected = {}

    for i, (a, b, ab, ba) in enumerate(rows):
        if i % 3 == 0:
            mixed_rows.append((a, b, ab))
            expected[a, b] = ab
            expected[b, a] = ab
        else:
            mixed_rows.append((a, b, ab, ba))
            expected[a, b] = ab
            expected[b, a] = ba

    with _files(
        experiment, parcels, trucks, mixed_rows
    ) as (paths, root):

        monkeypatch.chdir(root)

        dmap = experiment.read_distance_map(
            paths['map_file']
        )

        for (a, b), distance in expected.items():
            assert dmap.distance(a, b) == distance

        assert dmap.distance(
            'Missing', 'Depot'
        ) == -1


# =========================================================
# READ TRUCKS
# =========================================================

@pytest.mark.target_method('read_trucks')
@pytest.mark.parametrize('case', range(10))
def test_reader_trucks_10_scenarios(
    case, monkeypatch
):
    import experiment
    from domain import Parcel

    parcels, trucks, rows, _, _ = _scenario(case)

    with _files(
        experiment, parcels, trucks, rows
    ) as (paths, root):

        monkeypatch.chdir(root)

        fleet = experiment.read_trucks(
            paths['truck_file'], 'Depot'
        )

        assert fleet.num_trucks() == len(trucks)

        assert fleet.parcel_allocations() == {
            tid: [] for tid, _ in trucks
        }

        # Fleet.trucks is a documented public attribute.
        for i, (
            (tid, capacity), truck
        ) in enumerate(zip(trucks, fleet.trucks)):

            assert truck.fullness() == pytest.approx(0)

            assert truck.pack(
                Parcel(
                    i + 1, capacity,
                    'Origin', f'Dest-{i}'
                )
            )

            assert truck.fullness() == pytest.approx(100)

        assert fleet.parcel_allocations() == {
            tid: [i + 1]
            for i, (tid, _) in enumerate(trucks)
        }


# =========================================================
# GREEDY SCHEDULER
# =========================================================

@pytest.mark.target_method('GreedyScheduler.schedule')
@pytest.mark.parametrize('case', range(10))
def test_greedy_10_diverse_scenarios(
    case, monkeypatch
):
    import experiment

    parcels, trucks, rows, distances, _ = _scenario(
        case
    )

    options = (
        ('volume', 'destination')[case % 2],
        (
            'non-decreasing', 'non-increasing'
        )[(case // 2) % 2],
        (
            'non-decreasing', 'non-increasing'
        )[(case // 4) % 2]
    )

    expected, left, _ = _greedy_expected(
        parcels, trucks, distances, options
    )

    with _files(
        experiment, parcels, trucks, rows
    ) as (paths, root):

        monkeypatch.chdir(root)

        e = experiment.SchedulingExperiment(
            _config(paths, options)
        )

        input_parcels = e.parcels[:]
        input_trucks = e.fleet.trucks[:]

        actual_left = e.scheduler.schedule(
            e.parcels, e.fleet.trucks
        )

        assert e.fleet.parcel_allocations() == expected

        # Identify unscheduled parcels by object identity.
        source_by_identity = {
            id(p): parcels[i][0]
            for i, p in enumerate(input_parcels)
        }

        assert [
            source_by_identity[id(p)]
            for p in actual_left
        ] == left

        assert all(
            a is b
            for a, b in zip(e.parcels, input_parcels)
        )

        assert all(
            a is b
            for a, b in zip(
                e.fleet.trucks, input_trucks
            )
        )


# =========================================================
# RANDOM SCHEDULER
# =========================================================

@pytest.mark.target_method('RandomScheduler.schedule')
@pytest.mark.parametrize('case', range(10))
def test_random_10_diverse_scenarios(
    case, monkeypatch
):
    import experiment

    parcels, trucks, rows, _, _ = _scenario(
        case, 1 + 13 * case
    )

    with _files(
        experiment, parcels, trucks, rows
    ) as (paths, root):

        monkeypatch.chdir(root)

        e = experiment.SchedulingExperiment(
            _config(paths, algorithm='random')
        )

        in_parcels = e.parcels[:]
        in_trucks = e.fleet.trucks[:]

        previous = random.getstate()

        try:
            random.seed(10000 + case)

            leftovers = e.scheduler.schedule(
                e.parcels, e.fleet.trucks
            )
        finally:
            random.setstate(previous)

        all_ids = [
            pid
            for ids in e.fleet.parcel_allocations().values()
            for pid in ids
        ]

        by_identity = {
            id(p): parcels[i][0]
            for i, p in enumerate(in_parcels)
        }

        leftover_ids = [
            by_identity[id(p)]
            for p in leftovers
        ]

        assert sorted(
            all_ids + leftover_ids
        ) == sorted(
            row[0] for row in parcels
        )

        assert len(all_ids) == len(set(all_ids))

        assert all(
            a is b
            for a, b in zip(e.parcels, in_parcels)
        )

        assert all(
            a is b
            for a, b in zip(
                e.fleet.trucks, in_trucks
            )
        )

        capacities = dict(trucks)

        volumes = {
            pid: volume
            for pid, _, _, volume in parcels
        }

        available = {
            tid: capacities[tid] - sum(
                volumes[pid] for pid in ids
            )
            for tid, ids in
            e.fleet.parcel_allocations().items()
        }

        assert all(
            space >= 0
            for space in available.values()
        )

        for pid in leftover_ids:
            assert all(
                space < volumes[pid]
                for space in available.values()
            )


# =========================================================
# SCHEDULING EXPERIMENT
# =========================================================

@pytest.mark.target_method('SchedulingExperiment.run')
@pytest.mark.parametrize('case', range(10))
def test_experiment_10_full_statistics_scenarios(
    case, monkeypatch
):
    import experiment

    parcels, trucks, rows, distances, _ = _scenario(
        case, 8 + 13 * case
    )

    options = (
        ('volume', 'destination')[case % 2],
        (
            'non-decreasing', 'non-increasing'
        )[(case // 2) % 2],
        (
            'non-decreasing', 'non-increasing'
        )[(case // 4) % 2]
    )

    expected_allocation, _, expected_stats = (
        _greedy_expected(
            parcels, trucks, distances, options
        )
    )

    with _files(
        experiment, parcels, trucks, rows
    ) as (paths, root):

        monkeypatch.chdir(root)

        e = experiment.SchedulingExperiment(
            _config(paths, options)
        )

        actual = e.run()

        assert (
            e.fleet.parcel_allocations()
            == expected_allocation
        )

        for key, expected in expected_stats.items():
            assert key in actual

            if isinstance(expected, float):
                assert actual[key] == pytest.approx(
                    expected
                ), (
                    key, actual[key], expected
                )
            else:
                assert actual[key] == expected, (
                    key, actual[key], expected
                )

@pytest.mark.target_method("SchedulingExperiment.__init__")
@pytest.mark.parametrize("case", range(10))
def test_experiment_constructor_public_behavior(case, monkeypatch):
    import experiment
    from scheduler import GreedyScheduler, RandomScheduler

    parcels, trucks, rows, distances, cities = _scenario(
        case, count=1 + case * 15
    )

    options = (
        ("volume", "destination")[case % 2],
        ("non-decreasing", "non-increasing")[(case // 2) % 2],
        ("non-decreasing", "non-increasing")[(case // 4) % 2]
    )

    algorithm = "random" if case in (3, 7, 9) else "greedy"

    with _files(
        experiment, parcels, trucks, rows
    ) as (paths, root):

        monkeypatch.chdir(root)

        config = _config(
            paths,
            options=options,
            algorithm=algorithm
        )

        e = experiment.SchedulingExperiment(config)

        expected_scheduler = (
            RandomScheduler
            if algorithm == "random"
            else GreedyScheduler
        )

        assert isinstance(e.scheduler, expected_scheduler)

        assert len(e.parcels) == len(parcels)

        assert e.fleet.num_trucks() == len(trucks)

        assert e.fleet.num_nonempty_trucks() == 0

        assert e.fleet.parcel_allocations() == {
            tid: [] for tid, capacity in trucks
        }

        # Confirm that the constructor loaded the map.
        a, b, forward, backward = rows[0]

        assert e.dmap.distance(a, b) == forward
        assert e.dmap.distance(b, a) == backward
