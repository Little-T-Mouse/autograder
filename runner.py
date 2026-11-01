"""Python-side test collector; executed by Pyodide inside a browser Web Worker."""
import contextlib
import io
import json
import os
import sys

import pytest


class Reporter:
    def __init__(self):
        self.tests = {}
        self.collection_errors = []

    def pytest_runtest_logreport(self, report):
        key = report.nodeid
        if report.when == 'call' or (report.failed and report.when in ('setup', 'teardown')) or (report.skipped and report.when == 'setup'):
            self.tests[key] = {
                'name': key.split('::')[-1],
                'path': key,
                'status': 'passed' if report.passed else ('skipped' if report.skipped else 'failed'),
                'details': '' if report.passed else report.longreprtext[-3000:],
                'duration': round(report.duration, 3),
            }

    def pytest_collectreport(self, report):
        if report.failed:
            self.collection_errors.append({
                'name': 'Collection: ' + report.nodeid,
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
    with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
        try:
            exit_code = int(pytest.main([
                '/grader_tests', '-q', '--tb=short', '--disable-warnings',
                '-p', 'no:cacheprovider', '-p', 'no:faulthandler',
            ], plugins=[reporter]))
        except BaseException as exc:
            return json.dumps({'ok': False, 'error': f'{type(exc).__name__}: {exc}'})
    outcomes = list(reporter.tests.values()) + reporter.collection_errors
    counts = {name: sum(1 for r in outcomes if r['status'] == name)
              for name in ('passed', 'failed', 'skipped')}
    return json.dumps({
        'ok': True,
        'exitCode': exit_code,
        'results': outcomes,
        'counts': counts,
        'output': captured.getvalue()[-5000:],
    })


__grading_result = grade()
