
"""Independent A1 practice tests for CSV readers and end-to-end experiments.

Produces its own synthetic city graph, trucks and parcels in temporary files.
The independent expected statistics are calculated from simple Python lists.
"""

import csv
import random

import pytest


@pytest.mark.parametrize('seed', range(6))
def test_readers_accept_many_rows_and_hyphenated_city_names(seed, tmp_path, monkeypatch):
    import experiment
    rng = random.Random(seed)
    cities = ['Depot', 'A-B', 'A', 'B-C', 'City 01'] + [f'City-{i}' for i in range(25)]
    parcels = [(i + 1, 'Origin', rng.choice(cities[1:]), rng.randint(1, 12))
               for i in range(130)]
    trucks = [(i + 100, rng.randint(50, 100)) for i in range(15)]
    distances = []
    for i, a in enumerate(cities):
        for b in cities[i + 1:]:
            distances.append((a, b, rng.randint(1, 300), rng.randint(1, 300)))
    for filename, rows in [('parcels.csv', parcels), ('trucks.csv', trucks),
                           ('distances.csv', distances)]:
        with (tmp_path / filename).open('w', newline='', encoding='utf8') as file:
            csv.writer(file).writerows(rows)
    monkeypatch.setattr(experiment, 'PATH', str(tmp_path) + '/')
    actual_parcels = experiment.read_parcels('parcels.csv')
    actual_fleet = experiment.read_trucks('trucks.csv', 'Depot')
    actual_map = experiment.read_distance_map('distances.csv')
    assert [(p.id_, p.source, p.destination, p.volume) for p in actual_parcels] == parcels
    assert [(t.id_, t.capacity) for t in actual_fleet.trucks] == trucks
    assert all(t.route == ['Depot'] and t.used_space == 0 for t in actual_fleet.trucks)
    for a, b, forward, backward in distances:
        assert actual_map.distance(a, b) == forward
        assert actual_map.distance(b, a) == backward


def test_read_distance_map_three_column_symmetric_and_four_column_directed(tmp_path, monkeypatch):
    import experiment
    with (tmp_path / 'distances.csv').open('w', newline='', encoding='utf8') as file:
        csv.writer(file).writerows([
            ('A-B', 'C', 11),
            ('A', 'B-C', 27, 33),
            ('Depot', 'A-B', 0, 12),
        ])
    monkeypatch.setattr(experiment, 'PATH', str(tmp_path) + '/')
    m = experiment.read_distance_map('distances.csv')
    assert m.distance('A-B', 'C') == 11
    assert m.distance('C', 'A-B') == 11
    assert m.distance('A', 'B-C') == 27
    assert m.distance('B-C', 'A') == 33
    assert m.distance('Depot', 'A-B') == 0
    assert m.distance('A-B', 'Depot') == 12


def _reference_stats(parcels, trucks, distances, config):
    """Compute the experiment expected values without importing student code."""
    order_key = (lambda p: p[3]) if config['parcel_priority'] == 'volume' else (lambda p: p[2])
    ordered = sorted(parcels, key=order_key,
                     reverse=config['parcel_order'] == 'non-increasing')
    capacities = [capacity for _, capacity in trucks]
    used = [0] * len(trucks)
    routes = [['Depot'] for _ in trucks]
    unscheduled = 0
    for _, _, destination, volume in ordered:
        eligible = [i for i, capacity in enumerate(capacities)
                    if capacity - used[i] >= volume]
        if not eligible:
            unscheduled += 1
            continue
        matching = [i for i in eligible if routes[i][-1] == destination]
        if matching:
            eligible = matching
        if config['truck_order'] == 'non-decreasing':
            chosen = min(eligible, key=lambda i: capacities[i] - used[i])
        else:
            chosen = max(eligible, key=lambda i: capacities[i] - used[i])
        used[chosen] += volume
        if routes[chosen][-1] != destination:
            routes[chosen].append(destination)
    occupied = [i for i, volume in enumerate(used) if volume > 0]
    assert occupied, 'The generated scenario must have at least one used truck'
    traveled = []
    for i in occupied:
        route = routes[i]
        traveled.append(sum(distances[route[j], route[j + 1]]
                            for j in range(len(route) - 1)) +
                        distances[route[-1], route[0]])
    return {
        'fleet': len(trucks),
        'unused_trucks': len(trucks) - len(occupied),
        'unscheduled': unscheduled,
        'unused_space': sum(capacities[i] - used[i] for i in occupied),
        'avg_fullness': sum(used[i] / capacities[i] * 100 for i in occupied) / len(occupied),
        'avg_distance': sum(traveled) / len(traveled),
    }


@pytest.mark.parametrize('seed', (1, 2, 3, 4))
@pytest.mark.parametrize('priority', ('volume', 'destination'))
@pytest.mark.parametrize('parcel_order', ('non-decreasing', 'non-increasing'))
@pytest.mark.parametrize('truck_order', ('non-decreasing', 'non-increasing'))
def test_multicity_experiment_vs_independent_reference(
        seed, priority, parcel_order, truck_order, tmp_path, monkeypatch):
    import experiment
    rng = random.Random(seed)
    cities = ['Depot', 'A-B', 'A', 'B-C'] + [f'City-{i:02}' for i in range(18)]
    parcels = [(i + 1, 'Origin', rng.choice(cities[1:]), rng.randint(1, 30))
               for i in range(80)]
    trucks = [(100 + i, 100 if i == 0 else rng.randint(30, 120)) for i in range(14)]
    distances = {}
    distance_rows = []
    for i, city_a in enumerate(cities):
        for city_b in cities[i + 1:]:
            forward, backward = rng.randint(1, 300), rng.randint(1, 300)
            distance_rows.append((city_a, city_b, forward, backward))
            distances[city_a, city_b] = forward
            distances[city_b, city_a] = backward
    for filename, rows in [('parcels.csv', parcels), ('trucks.csv', trucks),
                           ('distances.csv', distance_rows)]:
        with (tmp_path / filename).open('w', newline='', encoding='utf8') as file:
            csv.writer(file).writerows(rows)
    monkeypatch.setattr(experiment, 'PATH', str(tmp_path) + '/')
    config = {
        'depot_location': 'Depot', 'parcel_file': 'parcels.csv',
        'truck_file': 'trucks.csv', 'map_file': 'distances.csv',
        'algorithm': 'greedy', 'parcel_priority': priority,
        'parcel_order': parcel_order, 'truck_order': truck_order,
    }
    expected = _reference_stats(parcels, trucks, distances, config)
    actual = experiment.SchedulingExperiment(config).run()
    assert set(expected) <= set(actual)
    for key, value in expected.items():
        if isinstance(value, float):
            assert actual[key] == pytest.approx(value), (key, actual[key], value)
        else:
            assert actual[key] == value, (key, actual[key], value)
