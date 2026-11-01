"""Experiment practice tests with independently generated tiny data files."""
import pytest


def test_experiment_exposes_correct_statistics_and_unscheduled_count(tmp_path, monkeypatch):
    import experiment
    # Build fresh in-memory data. No instructor-provided sample files are used.
    (tmp_path / 'parcels.csv').write_text('1,Base,Aspen,6\n2,Base,Birch,10\n', encoding='utf8')
    (tmp_path / 'trucks.csv').write_text('12,8\n13,100\n', encoding='utf8')
    (tmp_path / 'map.csv').write_text('Base,Aspen,4\nBase,Birch,9\nAspen,Birch,5\n', encoding='utf8')
    monkeypatch.setattr(experiment, 'PATH', str(tmp_path) + '/')
    options = {
        'depot_location': 'Base', 'parcel_file': 'parcels.csv',
        'truck_file': 'trucks.csv', 'map_file': 'map.csv',
        'algorithm': 'greedy', 'parcel_priority': 'volume',
        'parcel_order': 'non-decreasing', 'truck_order': 'non-decreasing',
    }
    scenario = experiment.SchedulingExperiment(options)
    data = scenario.run()
    assert data['fleet'] == 2
    assert data['unused_trucks'] == 0
    assert data['unscheduled'] == 0
    assert data['avg_distance'] == pytest.approx(13)
    assert data['avg_fullness'] == pytest.approx(42.5)
    assert data['unused_space'] == 92


def test_experiment_counts_unassigned_packages(tmp_path, monkeypatch):
    import experiment
    (tmp_path / 'packages.csv').write_text('5,Base,Oak,4\n6,Base,Elm,12\n', encoding='utf8')
    (tmp_path / 'vehicles.csv').write_text('9,7\n', encoding='utf8')
    (tmp_path / 'distances.csv').write_text('Base,Oak,3\nBase,Elm,8\nOak,Elm,6\n', encoding='utf8')
    monkeypatch.setattr(experiment, 'PATH', str(tmp_path) + '/')
    options = {
        'depot_location': 'Base', 'parcel_file': 'packages.csv',
        'truck_file': 'vehicles.csv', 'map_file': 'distances.csv',
        'algorithm': 'greedy', 'parcel_priority': 'volume',
        'parcel_order': 'non-decreasing', 'truck_order': 'non-decreasing',
    }
    result = experiment.SchedulingExperiment(options).run()
    assert result['fleet'] == 1
    assert result['unused_trucks'] == 0
    assert result['unscheduled'] == 1
    assert result['unused_space'] == 3
    assert result['avg_fullness'] == pytest.approx(400 / 7)
    assert result['avg_distance'] == pytest.approx(6)
