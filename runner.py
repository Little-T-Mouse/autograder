
"""Python test collector for the browser-based autograder."""

import contextlib
import io
import json
import os
import sys

import pytest


# Classification for the existing A1 public-interface tests.
TARGET_BY_TEST = {
    'test_distance_city_names': 'DistanceMap.distance',
    'test_distance_keys_do_not_collide': 'DistanceMap.add_distance',
    'test_distance_asymmetry_and_update': 'DistanceMap.add_distance',
    'test_distance_dense_forty_city_map': 'DistanceMap.distance',
    'test_priority_queue_stable_order': 'PriorityQueue.add',
    'test_priority_queue_interleaved_operations': 'PriorityQueue.remove',
    'test_truck_pack_through_public_methods': 'Truck.pack',
    'test_route_return_to_depot_and_revisited_city_by_total_distance':
        'Fleet.total_distance_travelled',
    'test_fleet_many_trucks_using_public_methods':
        'Fleet.parcel_allocations',
    'test_greedy_all_eight_modes_via_public_experiment_api':
        'GreedyScheduler.schedule',
    'test_random_scheduling_public_invariants':
        'RandomScheduler.schedule',
}


class Reporter:
    def __init__(self):
        self.tests = {}
        self.collection_errors = []
        self.targets = {}

    def pytest_configure(self, config):
        config.addinivalue_line(
            'markers',
            'target_method(name): primary public method tested'
        )

    def pytest_collection_modifyitems(self, items):
        for item in items:
            marker = item.get_closest_marker('target_method')

            if marker and marker.args and isinstance(
                marker.args[0], str
            ):
                method = marker.args[0]
            else:
                function_name = item.name.split('[', 1)[0]
                method = TARGET_BY_TEST.get(
                    function_name, 'Other tests'
                )

            self.targets[item.nodeid] = method

    def pytest_runtest_logreport(self, report):
        key = report.nodeid

        record = (
            report.when == 'call'
            or (
                report.failed
                and report.when in ('setup', 'teardown')
            )
            or (report.skipped and report.when == 'setup')
        )

        if record:
            self.tests[key] = {
                'name': key.split('::')[-1],
                'method': self.targets.get(key, 'Other tests'),
                'path': key,
                'status': (
                    'passed' if report.passed
                    else 'skipped' if report.skipped
                    else 'failed'
                ),
                'details': (
                    '' if report.passed
                    else report.longreprtext[-3000:]
                ),
                'duration': round(report.duration, 3),
            }

    def pytest_collectreport(self, report):
        if report.failed:
            self.collection_errors.append({
                'name': 'Collection: ' + report.nodeid,
                'method': 'Collection errors',
                'path': report.nodeid,
                'status': 'failed',
                'details': report.longreprtext[-3000:],
                'duration': 0,
            })


def grade():
    os.chdir('/submission')
    sys.path.insert(0, '/submission')

    reporter = Reporter()
    captured = io.StringIO()

    with contextlib.redirect_stdout(captured), \
            contextlib.redirect_stderr(captured):
        try:
            exit_code = int(pytest.main([
                '/grader_tests',
                '-q',
                '--tb=short',
                '--disable-warnings',
                '-p', 'no:cacheprovider',
                '-p', 'no:faulthandler',
            ], plugins=[reporter]))
        except BaseException as exc:
            return json.dumps({
                'ok': False,
                'error': f'{type(exc).__name__}: {exc}'
            })

    outcomes = (
        list(reporter.tests.values())
        + reporter.collection_errors
    )

    counts = {
        name: sum(
            r['status'] == name for r in outcomes
        )
        for name in ('passed', 'failed', 'skipped')
    }

    return json.dumps({
        'ok': True,
        'exitCode': exit_code,
        'results': outcomes,
        'counts': counts,
        'output': captured.getvalue()[-5000:],
    })


__grading_result = grade()
