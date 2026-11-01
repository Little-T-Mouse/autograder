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
  renderFileList();
  if (!a) return;
  assignmentDescription.textContent = a.description;
  if (a.status !== 'ready') {
    requiredDescription.textContent = `Not available yet. ${a.hint}`;
  } else {
    requiredDescription.textContent = `Required: ${a.requiredFiles.join(', ')}. Other .py files are also accepted.`;
  }
  sampleButton.hidden = a.id !== 'demo';
  showState('empty');
  updateRunButton();
}

function updateRunButton() {
  const a = selectedAssignment();
  const missing = a?.requiredFiles.filter(f => !uploads.has(f)) ?? [];
  runButton.disabled = running || !a || a.status !== 'ready' || uploads.size === 0 || missing.length > 0;
  if (a?.status === 'ready' && missing.length > 0 && uploads.size > 0) {
    requiredDescription.textContent = `Missing required file${missing.length > 1 ? 's' : ''}: ${missing.join(', ')}`;
  } else if (a?.status === 'ready') {
    requiredDescription.textContent = `Required: ${a.requiredFiles.join(', ')}. Other .py files are also accepted.`;
  }
}

function renderFileList() {
  fileList.replaceChildren();
  for (const name of uploads.keys()) {
    const li = document.createElement('li');
    li.textContent = name;
    fileList.appendChild(li);
  }
  updateRunButton();
}

async function addFiles(files) {
  if (running) return;
  let issue = '';
  for (const file of files) {
    if (!file.name.endsWith('.py') || file.name.includes('/') || file.name.includes('\\') || file.name === '.' || file.name === '..') {
      issue = 'Only files ending in .py are accepted.';
      continue;
    }
    if (file.size > 2 * 1024 * 1024) {
      issue = `${file.name} is too large. Maximum file size is 2 MB.`;
      continue;
    }
    const content = await file.text();
    uploads.set(file.name, { name: file.name, content });
  }
  if (uploads.size > 30 || [...uploads.values()].reduce((sum, file) => sum + file.content.length, 0) > 5 * 1024 * 1024) {
    uploads.clear();
    issue = 'Maximum submission: 30 Python files, 5 MB total.';
  }
  renderFileList();
  if (issue) displayError(issue);
  else showState('empty');
}

async function loadText(path) {
  const response = await fetch(path, { cache: 'no-store' });
  if (!response.ok) throw new Error(`Could not load ${path} (${response.status})`);
  return response.text();
}

function displayError(message) {
  showState('error');
  errorMessage.textContent = message;
}

// Run every submission in a fresh classic Web Worker. This avoids the
// initialization errors seen with module-worker imports on some hosts.
function executeInWorker(payload, onProgress, timeoutMs = 120000) {
  return new Promise((resolve, reject) => {
    let worker;
    try {
      worker = new Worker('./runner-worker.js?v=classic-1');
    } catch (error) {
      reject(new Error(`Could not create the Python worker: ${error.message}. Use a recent browser and serve this website over HTTP(S).`));
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
      if (data.kind === 'ready') { workerReady = true; onProgress('Python worker started. Preparing runtime…'); }
      else if (data.kind === 'progress') onProgress(data.message);
      else if (data.kind === 'complete') finish(null, data.result);
      else if (data.kind === 'error') finish(new Error(data.message));
    };
    worker.onerror = event => {
      const location = event.filename ? ` (${event.filename}:${event.lineno ?? '?'})` : '';
      finish(new Error(workerReady
        ? `The Python worker encountered a fatal error${location}: ${event.message || 'unknown error'}.`
        : `Your browser could not load runner-worker.js${location}: ${event.message || 'worker startup blocked'}. Make sure you uploaded runner-worker.js beside index.html and are using http://localhost or HTTPS, not file://. Check the Console for worker-src/CSP restrictions.`));
    };
    worker.onmessageerror = () => finish(new Error('The browser could not read a message from the Python worker.'));
    const timeout = setTimeout(() => finish(new Error('Tests timed out after 120 seconds. The Python runtime may be blocked by your network, or the uploaded code may contain an infinite loop.')), timeoutMs);
    worker.postMessage(payload);
  });
}

function renderResults(report) {
  if (!report?.ok) {
    displayError(report?.error || 'The test runner encountered an unexpected error.');
    return;
  }
  showState('results');
  const { passed = 0, failed = 0, skipped = 0 } = report.counts ?? {};
  const total = passed + failed + skipped;
  document.querySelector('#scoreText').textContent = `${passed} / ${total}`;
  document.querySelector('#scoreRate').textContent = `${total ? Math.round(passed / total * 100) : 0}%`;
  document.querySelector('#progressFill').style.width = `${total ? passed / total * 100 : 0}%`;
  document.querySelector('#passedCount').textContent = `${passed} passed`;
  document.querySelector('#failedCount').textContent = `${failed} failed`;
  document.querySelector('#skippedCount').textContent = `${skipped} skipped`;
  statusPill.textContent = failed > 0 || report.exitCode !== 0 ? 'Needs attention' : 'All passed';
  statusPill.classList.add(failed > 0 || report.exitCode !== 0 ? 'failure' : 'success');
  testResults.replaceChildren();
  for (const result of report.results ?? []) {
    const item = document.createElement('div');
    item.className = `test-result ${result.status}`;
    const line = document.createElement('div');
    line.className = 'test-line';
    const dot = document.createElement('div');
    dot.className = 'result-dot';
    dot.textContent = result.status === 'passed' ? '✓' : result.status === 'skipped' ? '–' : '✕';
    const name = document.createElement('div');
    name.className = 'test-name';
    name.textContent = result.name;
    name.title = result.path;
    const status = document.createElement('span');
    status.className = 'test-status';
    status.textContent = result.status;
    line.append(dot, name, status);
    item.appendChild(line);
    if (result.details) {
      const details = document.createElement('details');
      const summary = document.createElement('summary');
      summary.textContent = 'View error and debugging information';
      const pre = document.createElement('pre');
      pre.textContent = result.details;
      details.append(summary, pre);
      item.appendChild(details);
    }
    testResults.appendChild(item);
  }
  const raw = document.querySelector('#rawOutput');
  raw.hidden = !report.output;
  document.querySelector('#rawOutputText').textContent = report.output || '';
  if (!total) {
    const message = document.createElement('p');
    message.textContent = 'No tests were collected. Review the output and test configuration.';
    testResults.appendChild(message);
  }
}

async function runTests() {
  const a = selectedAssignment();
  if (!a || a.status !== 'ready' || runButton.disabled || running) return;
  running = true;
  updateRunButton();
  showState('running');
  progressMessage.textContent = 'Loading test cases…';
  try {
    const [runner, ...testContents] = await Promise.all([
      loadText('runner.py'), ...a.testFiles.map(loadText),
    ]);
    const tests = a.testFiles.map((path, i) => ({ name: path.split('/').pop(), content: testContents[i] }));
    if (new Set(tests.map(t => t.name)).size !== tests.length) {
      throw new Error('The assignment configuration includes duplicate test filenames.');
    }
    const report = await executeInWorker({
      runner, tests, files: Array.from(uploads.values()),
    }, message => { progressMessage.textContent = message; });
    renderResults(report);
  } catch (error) {
    displayError(String(error.message ?? error));
  } finally {
    running = false;
    updateRunButton();
  }
}

assignmentSelect.addEventListener('change', refreshAssignment);
fileInput.addEventListener('change', async () => {
  await addFiles(fileInput.files);
  fileInput.value = '';
});
for (const type of ['dragenter', 'dragover']) {
  dropzone.addEventListener(type, event => { event.preventDefault(); dropzone.classList.add('drag-over'); });
}
for (const type of ['dragleave', 'drop']) {
  dropzone.addEventListener(type, event => { event.preventDefault(); dropzone.classList.remove('drag-over'); });
}
dropzone.addEventListener('drop', event => addFiles(event.dataTransfer.files));
runButton.addEventListener('click', runTests);
sampleButton.addEventListener('click', async () => {
  assignmentSelect.value = 'demo';
  refreshAssignment();
  try {
    const content = await loadText('examples/solution.py');
    uploads.set('solution.py', { name: 'solution.py', content });
    renderFileList();
  } catch (error) { displayError(error.message); }
});

async function main() {
  try {
    const response = await fetch('assignments.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('Unable to load assignment configuration');
    const data = await response.json();
    assignmentSelect.replaceChildren();
    for (const a of data) {
      assignments.set(a.id, a);
      const option = document.createElement('option');
      option.value = a.id;
      option.textContent = a.title + (a.status !== 'ready' ? ' (not yet configured)' : '');
      assignmentSelect.appendChild(option);
    }
    assignmentSelect.value = data[0].id;
    refreshAssignment();
  } catch (error) {
    assignmentSelect.innerHTML = '<option>Unavailable</option>';
    displayError('Could not load the website configuration. Run it through an HTTP server (not as a file:// page).');
  }
}
main();
