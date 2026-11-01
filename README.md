# CSC148 Practice Autograder — starter website

A **free static website** where students choose an assignment, upload `.py` files, and run your publicly distributed pytest tests in their own browsers via Pyodide. No Python backend, database, or user accounts required.

> **Status:** A1 is now configured with **30 independent practice test cases** (26 test functions including parameterized cases) covering Tasks 1–5. The demo remains available, and A2 is reserved for a future assignment. The public ZIP contains no course-provided starter code, instructor tests, or submission solutions.

## Run locally

Requirements: Python 3 (for the local file server) and an internet connection (to download Pyodide and pytest).

```bash
cd csc148-practice-autograder
python -m http.server 8000
```

Visit <http://localhost:8000>. The site initially selects **A1 · Parcel Delivery Scheduler**. Upload the five files listed below and click **Run practice tests**. You can still select **Demo · List Utilities** to try the sample.

The initial runtime download can take a while. If it fails, the website distinguishes a worker-loading error from a Pyodide download/init error. The demo is intentionally expected to fail one parameterized case.

## A1 · Parcel Delivery Scheduler — Ready

Upload these five files from your own assignment workspace, with their original names:

- `container.py`
- `distance_map.py`
- `domain.py`
- `scheduler.py`
- `experiment.py`

These are **not included** in the public website package. `explore.py` and `generator.py` are unnecessary for the current practice tests. No course data files are needed; experiment tests synthesize their own small data.

### Current extra practice coverage

| Module / task | Tests focus on |
| --- | --- |
| Task 1: `distance_map.py` | Unknown distances, reverse direction, asymmetric routes, reassignments |
| Task 2: `domain.py` | Parcel attributes, exact capacity, failed packing, routes, fleet usage and statistics |
| Task 3: `container.py` | Priority queue sorting, reverse comparisons, stable ties and reuse |
| Task 4: `scheduler.py` | Four parcel order modes, two truck capacity preferences, destination matching, stable ties, random behavior, unscheduled parcels |
| Task 5: `experiment.py` | Generated temporary CSV data, correct statistics and unscheduled counts |

These are **practice tests** based on publicly describable behavior; they are not the official course tests, cannot establish full grading correctness, and do not verify every style/design requirement.

To expand your own suite, add an independently written `test_*.py` under `tests/a1/` and add its path to the A1 `testFiles` list in `assignments.json`. You can also edit the existing files. Each test module filename must be unique. Avoid importing tests or other files protected by course distribution restrictions.

### How to test locally with your own code

You can also run these tests with Python on your computer without the website:

```bash
python -m pytest /path/to/website/tests/a1 -q
```

Run this command from the directory containing your five A1 Python files, and ensure Python can import those files (for example, by setting `PYTHONPATH` to that directory). The tests are designed to run under both normal pytest and Pyodide.

### What was checked before packaging

- **30 of 30 practice cases passed** against a locally tested implementation from the user's earlier CSC148 code review. This is not course or official autograder verification.
- Python test collection and behavior were verified locally with pytest.
- The browser frontend was checked for JavaScript syntax, but the hosted Pyodide download and full browser execution could not be verified in the offline test environment. Run the demo in Chrome or Firefox before publishing.

## Publish to GitHub Pages

1. Create a GitHub repository (for example, `csc148-practice-grader`).
2. Upload all files in this project **without an extra top-level directory**, so `index.html` sits at the repo root.
3. Go to **Settings → Pages → Build and deployment → Deploy from a branch**.
4. Choose `main` and `/ (root)`, then save.
5. After GitHub publishes, your site will be at `https://YOUR-USERNAME.github.io/csc148-practice-grader/` (assuming that repository name).

GitHub Pages serves static HTML/CSS/JavaScript; Pyodide runs the Python tests on each student's browser. There is no per-submission server processing to pay for.

## Safety & limitations

- **Browser-only execution is not a secure code-execution service.** This prototype executes submissions inside a dedicated browser Web Worker at the same origin as the static website, not in an iframe sandbox. Web Workers do not have DOM access, but **are not a secure sandbox for adversarial Python code**; Pyodide allows JavaScript interoperability. Users should only upload code they trust, and the site must not host authenticated or private data at the same origin. To safely execute arbitrary adversarial submissions, use a separate hardened execution origin or properly isolated backend.
- **No backend receives code**, but the browser necessarily reads student uploads and the runner itself has in-memory access to them. Avoid asking for personal data, secrets, or unrelated files.
- Anyone can read/download your public test cases; use a real server-side grader for secret tests or authoritative grading.
- Pyodide cannot use every CPython binary extension or OS feature. Test actual CSC148 submissions for compatibility before releasing.
- This is **not** an official grader; passing all of your tests does not guarantee an assignment is correct.
- A submission has a **120-second total timeout** to cover both Python setup and execution. The Web Worker is terminated after finishing or timing out.
- Files are not stored in a database. Refreshing the page clears uploads and test results.
- Check course policies and licensing before sharing tests or starter code. Do not publish instructor-provided tests, solutions, or copyrighted course files without permission.

## Files

- `index.html`, `styles.css`, `app.js` — student interface.
- `assignments.json` — assignment choices, filenames, and test paths.
- `runner-worker.js` — same-origin classic Pyodide Web Worker for Python execution.
- `runner.py` — pytest results collector producing JSON.
- `tests/` — your public test files, organized by assignment.
- `examples/solution.py` — intentionally buggy sample code for the demo.

## Troubleshooting: worker startup

The worker is now a **classic** worker, not a module worker. After replacing all website files, hard-refresh with Ctrl+Shift+R.

- If the message says `Could not download Pyodide JavaScript`, visit <https://cdn.jsdelivr.net/pyodide/v0.29.5/full/pyodide.js> in the browser running the site. If this URL cannot load, the network is blocking Python runtime downloads; changing JavaScript alone cannot fix that.
- If the message says `could not load runner-worker.js`, verify that `runner-worker.js` is beside `index.html` on your hosting service and that you serve the site with HTTP(S), not `file://`. Check the browser console for content security policy (CSP) issues.
- If it hangs at `Starting Python`, the initial WebAssembly/stdlib download may be blocked; inspect failed network requests in DevTools.
- In a production deployment, you can avoid a third-party CDN dependency by serving a matching Pyodide release's runtime and pytest wheel assets yourself and changing `PYODIDE_BASE` to the local URL. This requires extra storage and configuration.

**Verification:** JavaScript syntax and local pytest cases were tested. Browser end-to-end Pyodide download couldn't be tested inside the available restricted browser environment, so this is a targeted fix, not a guarantee that your browser/network permits the runtime.
