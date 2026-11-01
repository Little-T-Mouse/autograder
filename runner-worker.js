// Classic Worker: avoids browser restrictions on module-worker loading.
// This file must be served from the same site as index.html (HTTP or HTTPS).
'use strict';

const PYODIDE_BASE = 'https://cdn.jsdelivr.net/pyodide/v0.29.5/full/';

// This runs before any external downloads. If this message is received, the
// browser successfully loaded our worker script.
self.postMessage({ kind: 'ready' });

self.onmessage = async (event) => {
  const { files, tests, runner } = event.data || {};
  if (!Array.isArray(files) || !Array.isArray(tests) || typeof runner !== 'string') {
    self.postMessage({ kind: 'error', message: 'Invalid test-runner request.' });
    return;
  }

  try {
    self.postMessage({ kind: 'progress', message: 'Loading Python runtime from the Pyodide CDN…' });

    // importScripts is available in classic Workers, not module Workers.
    // Unlike a top-level ESM import, this can be caught and reported back.
    // It also avoids the module-worker failure in some browser/hosting setups.
    try {
      importScripts(PYODIDE_BASE + 'pyodide.js');
    } catch (error) {
      throw new Error(
        'Could not download Pyodide JavaScript. Try opening ' +
        PYODIDE_BASE + 'pyodide.js in this browser. If it is blocked, ' +
        'disable network blockers or use a network that allows cdn.jsdelivr.net. ' +
        'Browser details: ' + String(error && error.message || error)
      );
    }
    if (typeof self.loadPyodide !== 'function') {
      throw new Error('The Pyodide loader downloaded but did not initialize correctly.');
    }
    self.postMessage({ kind: 'progress', message: 'Starting Python (first run can take longer)…' });
    const pyodide = await self.loadPyodide({ indexURL: PYODIDE_BASE });

    self.postMessage({ kind: 'progress', message: 'Loading pytest…' });
    await pyodide.loadPackage('pytest');
    pyodide.FS.mkdir('/submission');
    pyodide.FS.mkdir('/grader_tests');

    for (const file of files) {
      // Files are checked by the UI but are validated again here.
      if (!/^[A-Za-z0-9_.-]+\.py$/.test(file.name) || file.name.length > 120) {
        throw new Error('Invalid Python filename: ' + String(file.name));
      }
      pyodide.FS.writeFile('/submission/' + file.name, file.content, { encoding: 'utf8' });
    }
    for (const test of tests) {
      if (!/^[A-Za-z0-9_.-]+\.py$/.test(test.name)) {
        throw new Error('Invalid test filename.');
      }
      pyodide.FS.writeFile('/grader_tests/' + test.name, test.content, { encoding: 'utf8' });
    }
    pyodide.FS.writeFile('/runner.py', runner, { encoding: 'utf8' });

    self.postMessage({ kind: 'progress', message: 'Running practice tests…' });
    const json = await pyodide.runPythonAsync(
      "import runpy\nrunpy.run_path('/runner.py')['__grading_result']",
      { filename: '/runner.py' }
    );
    self.postMessage({ kind: 'complete', result: JSON.parse(json) });
  } catch (error) {
    // Include a useful traceback if Python/pytest fails after worker startup.
    self.postMessage({ kind: 'error', message: String(error?.stack || error) });
  }
};
