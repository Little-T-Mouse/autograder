
'use strict';

const assignmentSelect = document.querySelector('#assignment');
const assignmentDescription = document.querySelector('#assignmentDescription');
const requiredDescription = document.querySelector('#requiredDescription');
const fileInput = document.querySelector('#fileInput');
const dropzone = document.querySelector('#dropzone');
const fileList = document.querySelector('#fileList');
const runButton = document.querySelector('#runButton');
const sampleButton = document.querySelector('#sampleButton');
const statusPill = document.querySelector('#statusPill');
const emptyState = document.querySelector('#emptyState');
const runningState = document.querySelector('#runningState');
const resultsSection = document.querySelector('#results');
const errorState = document.querySelector('#errorState');
const progressMessage = document.querySelector('#progressMessage');
const errorMessage = document.querySelector('#errorMessage');
const testResults = document.querySelector('#testResults');

const uploadNotice = document.createElement('p');
uploadNotice.className = 'upload-notice';
uploadNotice.setAttribute('role', 'status');
uploadNotice.hidden = true;
fileList.after(uploadNotice);

function setUploadNotice(message, isError = false) {
  uploadNotice.textContent = message;
  uploadNotice.classList.toggle('error', isError);
  uploadNotice.hidden = !message;
}

const assignments = new Map();
let uploads = new Map();
let running = false;

function selectedAssignment() {
  return assignments.get(assignmentSelect.value);
}

function showState(state) {
  emptyState.hidden = state !== 'empty';
  runningState.hidden = state !== 'running';
  resultsSection.hidden = state !== 'results';
  errorState.hidden = state !== 'error';
  statusPill.className = 'status-pill';

  if (state === 'empty') statusPill.textContent = 'Not started';

  if (state === 'running') {
    statusPill.classList.add('running');
    statusPill.textContent = 'Running';
  }

  if (state === 'error') {
    statusPill.classList.add('failure');
    statusPill.textContent = 'Error';
  }
}

function refreshAssignment() {
  const a = selectedAssignment();

  uploads = new Map();
  fileInput.value = '';
  setUploadNotice('');

  if (!a) {
    renderFileList();
    return;
  }

  assignmentDescription.textContent = a.description || '';
  assignmentDescription.hidden = !a.description;

  sampleButton.hidden = a.id !== 'demo';
  showState('empty');
  renderFileList();
}

function renderRequiredFiles() {
  const a = selectedAssignment();
  requiredDescription.replaceChildren();

  if (!a) return;

  if (a.status !== 'ready') {
    const message = document.createElement('p');
    message.className = 'required-message';
    message.textContent =
      a.hint || 'This assignment is not available yet.';

    requiredDescription.appendChild(message);
    return;
  }

  const required = a.requiredFiles;
  const uploaded = required.filter(
    name => uploads.has(name)
  ).length;

  const missing = required.length - uploaded;

  const heading = document.createElement('div');
  heading.className = 'required-heading';

  const title = document.createElement('strong');
  title.textContent = 'Required files';

  const counter = document.createElement('span');
  counter.className = 'required-counter';
  counter.textContent =
    `${uploaded} / ${required.length} uploaded`;

  heading.append(title, counter);

  const list = document.createElement('ul');
  list.className = 'required-grid';

  for (const name of required) {
    const isUploaded = uploads.has(name);

    const item = document.createElement('li');
    item.className =
      `required-item ${isUploaded ? 'uploaded' : 'missing'}`;

    const symbol = document.createElement('span');
    symbol.className = 'required-symbol';
    symbol.textContent = isUploaded ? '✓' : '○';
    symbol.setAttribute('aria-hidden', 'true');

    const filename = document.createElement('span');
    filename.className = 'required-filename';
    filename.textContent = name;

    const state = document.createElement('span');
    state.className = 'required-item-state';
    state.textContent = isUploaded ? 'Added' : 'Missing';

    item.append(symbol, filename, state);
    list.appendChild(item);
  }

  const note = document.createElement('p');
  note.className =
    `required-message ${missing === 0 ? 'complete' : ''}`;

  note.textContent = missing === 0
    ? 'All files uploaded. Ready to run tests.'
    : `Upload ${missing} more ${
        missing === 1 ? 'file' : 'files'
      } to run tests.`;

  requiredDescription.append(heading, list, note);
}

function updateRunButton() {
  const a = selectedAssignment();
  const ready = a?.status === 'ready';
  const required = ready ? a.requiredFiles : [];

  const complete =
    ready &&
    required.length > 0 &&
    required.every(name => uploads.has(name)) &&
    uploads.size === required.length;

  runButton.disabled = running || !complete;
  fileInput.disabled = running || !ready;
  assignmentSelect.disabled = running;
  sampleButton.disabled = running;

  dropzone.classList.toggle(
    'unavailable',
    fileInput.disabled
  );

  fileList.querySelectorAll('.remove-file').forEach(
    button => {
      button.disabled = running;
    }
  );

  renderRequiredFiles();
}

function renderFileList() {
  fileList.replaceChildren();

  for (const name of uploads.keys()) {
    const li = document.createElement('li');

    const label = document.createElement('span');
    label.textContent = name;

    const removeButton = document.createElement('button');
    removeButton.type = 'button';
    removeButton.className = 'remove-file';
    removeButton.textContent = '×';
    removeButton.title = `Remove ${name}`;
    removeButton.setAttribute(
      'aria-label',
      `Remove ${name}`
    );
    removeButton.disabled = running;

    removeButton.addEventListener('click', () => {
      if (running) return;

      uploads.delete(name);
      fileInput.value = '';

      // Previous test results no longer apply.
      showState('empty');

      renderFileList();
      setUploadNotice(`${name} removed.`);
    });

    li.append(label, removeButton);
    fileList.appendChild(li);
  }

  updateRunButton();
}

async function addFiles(files) {
  if (running) return;

  const a = selectedAssignment();

  if (!a || a.status !== 'ready') {
    setUploadNotice(
      'This assignment is not accepting submissions yet.',
      true
    );
    return;
  }

  const assignmentId = a.id;
  const allowed = new Set(a.requiredFiles);

  const rejected = [];
  let accepted = 0;
  let replaced = 0;

  for (const file of Array.from(files)) {
    const name = file.name;

    // Only accept filenames required by this assignment.
    // Filenames are case-sensitive.
    if (!allowed.has(name)) {
      rejected.push(
        `${name}: not required for ${a.title}.`
      );
      continue;
    }

    // Validate Python filename.
    if (!/^[A-Za-z0-9_.-]+\.py$/.test(name) ||
        name.length > 120) {
      rejected.push(
        `${name}: invalid Python filename.`
      );
      continue;
    }

    // Limit each file to 2 MB.
    if (file.size > 2 * 1024 * 1024) {
      rejected.push(
        `${name}: larger than the 2 MB per-file limit.`
      );
      continue;
    }

    // Limit total submission to 5 MB.
    const currentSize = [...uploads.values()].reduce(
      (sum, uploaded) =>
        sum + (uploaded.size ??
          new Blob([uploaded.content]).size),
      0
    );

    const previousSize = uploads.get(name)?.size ?? 0;

    if (currentSize - previousSize + file.size >
        5 * 1024 * 1024) {
      rejected.push(
        `${name}: would exceed the 5 MB total limit.`
      );
      continue;
    }

    try {
      const content = await file.text();

      // Ignore uploads if the assignment changed.
      if (selectedAssignment()?.id !== assignmentId) {
        return;
      }

      if (uploads.has(name)) {
        replaced++;
      }

      uploads.set(name, {
        name,
        content,
        size: file.size
      });

      accepted++;

    } catch (error) {
      rejected.push(
        `${name}: could not read the file (${error.message}).`
      );
    }
  }

  // Reset previous feedback if code was changed.
  if (accepted) {
    showState('empty');
  }

  renderFileList();

  if (rejected.length) {
    setUploadNotice(
      `Rejected ${rejected.length} file(s):\n` +
      rejected.join('\n') +
      '\nUpload only the required files listed above.',
      true
    );

  } else if (accepted) {
    setUploadNotice(
      `${accepted} file(s) accepted` +
      (replaced ? ` (${replaced} replaced)` : '') +
      '.'
    );
  }
}

async function loadText(path) {
  const response = await fetch(
    path,
    { cache: 'no-store' }
  );

  if (!response.ok) {
    throw new Error(
      `Could not load ${path} (${response.status})`
    );
  }

  return response.text();
}

function displayError(message) {
  showState('error');
  errorMessage.textContent = message;
}

// Run every submission in a fresh classic Web Worker.
// This avoids module-worker initialization errors.
function executeInWorker(
  payload,
  onProgress,
  timeoutMs = 120000
) {
  return new Promise((resolve, reject) => {
    let worker;

    try {
      worker = new Worker(
        './runner-worker.js?v=classic-1'
      );
    } catch (error) {
      reject(new Error(
        `Could not create the Python worker: ${
          error.message
        }. Use a recent browser and serve this website over HTTP(S).`
      ));
      return;
    }

    let settled = false;
    let workerReady = false;

    const cleanup = () => {
      clearTimeout(timeout);
      worker.terminate();
    };

    const finish = (error, report) => {
      if (settled) return;

      settled = true;
      cleanup();

      if (error) reject(error);
      else resolve(report);
    };

    worker.onmessage = ({ data }) => {
      if (!data || typeof data !== 'object') return;

      if (data.kind === 'ready') {
        workerReady = true;
        onProgress(
          'Python worker started. Preparing runtime…'
        );
      } else if (data.kind === 'progress') {
        onProgress(data.message);
      } else if (data.kind === 'complete') {
        finish(null, data.result);
      } else if (data.kind === 'error') {
        finish(new Error(data.message));
      }
    };

    worker.onerror = event => {
      const location = event.filename
        ? ` (${event.filename}:${event.lineno ?? '?'})`
        : '';

      finish(new Error(
        workerReady
          ? `The Python worker encountered a fatal error${location}: ${
              event.message || 'unknown error'
            }.`
          : `Your browser could not load runner-worker.js${location}: ${
              event.message || 'worker startup blocked'
            }. Make sure runner-worker.js is beside index.html and you are using HTTP(S), not file://.`
      ));
    };

    worker.onmessageerror = () => {
      finish(new Error(
        'The browser could not read a message from the Python worker.'
      ));
    };

    const timeout = setTimeout(() => {
      finish(new Error(
        'Tests timed out after 120 seconds. The Python runtime may be blocked by your network, or the uploaded code may contain an infinite loop.'
      ));
    }, timeoutMs);

    worker.postMessage(payload);
  });
}



const A1_PUBLIC_METHODS = [
  'DistanceMap.__init__',
  'DistanceMap.distance',
  'DistanceMap.add_distance',

  'PriorityQueue.add',
  'PriorityQueue.remove',
  'PriorityQueue.is_empty',

  'Parcel.__init__',

  'Truck.__init__',
  'Truck.pack',
  'Truck.fullness',

  'Fleet.__init__',
  'Fleet.add_truck',
  'Fleet.num_trucks',
  'Fleet.num_nonempty_trucks',
  'Fleet.parcel_allocations',
  'Fleet.total_unused_space',
  'Fleet.average_fullness',
  'Fleet.total_distance_travelled',
  'Fleet.average_distance_travelled',

  'GreedyScheduler.schedule',
  'RandomScheduler.schedule',

  'SchedulingExperiment.__init__',
  'SchedulingExperiment.run',

  'read_parcels',
  'read_distance_map',
  'read_trucks'
];


function renderOneTest(result) {
  const item = document.createElement('div');
  item.className = `test-result ${result.status}`;

  const line = document.createElement('div');
  line.className = 'test-line';

  const dot = document.createElement('div');
  dot.className = 'result-dot';
  dot.textContent =
    result.status === 'passed' ? '✓'
    : result.status === 'skipped' ? '–'
    : '✕';

  const name = document.createElement('div');
  name.className = 'test-name';
  name.textContent = result.name;
  name.title = result.path || '';

  const status = document.createElement('span');
  status.className = 'test-status';
  status.textContent = result.status;

  line.append(dot, name, status);
  item.appendChild(line);

  if (result.details) {
    const details = document.createElement('details');
    const summary = document.createElement('summary');

    summary.textContent =
      'View error and debugging information';

    const pre = document.createElement('pre');
    pre.textContent = result.details;

    details.append(summary, pre);
    item.appendChild(details);
  }

  return item;
}


function renderResults(report) {
  if (!report?.ok) {
    displayError(
      report?.error || 'The test runner encountered an error.'
    );
    return;
  }

  showState('results');

  const {
    passed = 0,
    failed = 0,
    skipped = 0
  } = report.counts ?? {};

  const total = passed + failed + skipped;

  document.querySelector('#scoreText').textContent =
    `${passed} / ${total}`;

  document.querySelector('#scoreRate').textContent =
    `${total ? Math.round(passed / total * 100) : 0}%`;

  document.querySelector('#progressFill').style.width =
    `${total ? passed / total * 100 : 0}%`;

  document.querySelector('#passedCount').textContent =
    `${passed} passed`;

  document.querySelector('#failedCount').textContent =
    `${failed} failed`;

  document.querySelector('#skippedCount').textContent =
    `${skipped} skipped`;

  const hasFailures = failed > 0 || report.exitCode !== 0;

  statusPill.textContent =
    hasFailures ? 'Needs attention' : 'All passed';

  statusPill.classList.add(
    hasFailures ? 'failure' : 'success'
  );

  testResults.replaceChildren();

  // Organize results by their primary target method.
  const groups = new Map();

  if (selectedAssignment()?.id === 'a1') {
    for (const method of A1_PUBLIC_METHODS) {
      groups.set(method, []);
    }
  }

  for (const result of report.results ?? []) {
    const method = result.method || 'Other tests';

    if (!groups.has(method)) {
      groups.set(method, []);
    }

    groups.get(method).push(result);
  }

  for (const [method, tests] of groups) {
    const correct = tests.filter(
      t => t.status === 'passed'
    ).length;

    const failures = tests.filter(
      t => t.status === 'failed'
    ).length;

    const skippedTests = tests.filter(
      t => t.status === 'skipped'
    ).length;

    // Collapsible method section
    const section = document.createElement('details');
    section.className = 'method-group';

    // Automatically expand failed methods.
    section.open = failures > 0;

    const header = document.createElement('summary');
    header.className = 'method-summary';

    const methodName = document.createElement('span');
    methodName.className = 'method-name';
    methodName.textContent = method;

    const counter = document.createElement('span');
    counter.className = 'method-count';

    if (tests.length === 0) {
      counter.textContent = 'Not tested';
    } else {
      counter.textContent =
        `${correct} / ${tests.length} passed`;

      if (skippedTests) {
        counter.textContent +=
          ` · ${skippedTests} skipped`;
      }
    }

    if (failures > 0) {
      counter.classList.add('has-failures');
    }

    header.append(methodName, counter);
    section.appendChild(header);

    if (tests.length > 0) {
      // Progress bar
      const bar = document.createElement('div');
      bar.className = 'method-progress';

      const fill = document.createElement('div');
      fill.className = 'method-progress-fill';

      fill.style.width =
        `${100 * correct / tests.length}%`;

      bar.appendChild(fill);
      section.appendChild(bar);

      // Individual tests
      const content = document.createElement('div');
      content.className = 'method-tests';

      for (const test of tests) {
        content.appendChild(renderOneTest(test));
      }

      section.appendChild(content);
    } else {
      const note = document.createElement('p');
      note.className = 'method-untested';
      note.textContent =
        'No dedicated practice test for this method yet.';

      section.appendChild(note);
    }

    testResults.appendChild(section);
  }

  const raw = document.querySelector('#rawOutput');
  raw.hidden = !report.output;

  document.querySelector('#rawOutputText').textContent =
    report.output || '';

  if (!total) {
    const message = document.createElement('p');
    message.textContent =
      'No tests were collected. Review the test configuration.';
    testResults.appendChild(message);
  }
}

async function runTests() {
  const a = selectedAssignment();

  if (
    !a ||
    a.status !== 'ready' ||
    runButton.disabled ||
    running
  ) {
    return;
  }

  running = true;
  updateRunButton();
  showState('running');

  progressMessage.textContent = 'Loading test cases…';

  try {
    const [runner, ...testContents] = await Promise.all([
      loadText('runner.py'),
      ...a.testFiles.map(loadText)
    ]);

    const tests = a.testFiles.map((path, i) => ({
      name: path.split('/').pop(),
      content: testContents[i]
    }));

    if (
      new Set(tests.map(t => t.name)).size !==
      tests.length
    ) {
      throw new Error(
        'The assignment configuration includes duplicate test filenames.'
      );
    }

    const report = await executeInWorker(
      {
        runner,
        tests,
        files: Array.from(uploads.values())
      },
      message => {
        progressMessage.textContent = message;
      }
    );

    renderResults(report);

  } catch (error) {
    displayError(
      String(error.message ?? error)
    );
  } finally {
    running = false;
    updateRunButton();
  }
}

assignmentSelect.addEventListener(
  'change',
  refreshAssignment
);

fileInput.addEventListener('change', async () => {
  await addFiles(fileInput.files);
  fileInput.value = '';
});

for (const type of ['dragenter', 'dragover']) {
  dropzone.addEventListener(type, event => {
    event.preventDefault();
    dropzone.classList.add('drag-over');
  });
}

for (const type of ['dragleave', 'drop']) {
  dropzone.addEventListener(type, event => {
    event.preventDefault();
    dropzone.classList.remove('drag-over');
  });
}

dropzone.addEventListener('drop', event => {
  addFiles(event.dataTransfer.files);
});

runButton.addEventListener('click', runTests);

sampleButton.addEventListener('click', async () => {
  if (running) return;

  assignmentSelect.value = 'demo';
  refreshAssignment();

  try {
    const content = await loadText(
      'examples/solution.py'
    );

    uploads.set('solution.py', {
      name: 'solution.py',
      content
    });

    renderFileList();
  } catch (error) {
    displayError(error.message);
  }
});

async function main() {
  try {
    const response = await fetch(
      'assignments.json',
      { cache: 'no-store' }
    );

    if (!response.ok) {
      throw new Error(
        'Unable to load assignment configuration'
      );
    }

    const data = await response.json();

    assignmentSelect.replaceChildren();

    for (const a of data) {
      assignments.set(a.id, a);

      const option = document.createElement('option');
      option.value = a.id;

      option.textContent =
        a.title +
        (a.status !== 'ready'
          ? ' (not yet configured)'
          : '');

      assignmentSelect.appendChild(option);
    }

    assignmentSelect.value = data[0].id;
    refreshAssignment();

  } catch (error) {
    assignmentSelect.innerHTML =
      '<option>Unavailable</option>';

    displayError(
      'Could not load the website configuration. Run it through an HTTP server (not as a file:// page).'
    );
  }
}

main();
