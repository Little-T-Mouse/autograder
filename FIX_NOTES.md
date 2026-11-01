# Worker-loading repair (classic Worker)

## Why the preceding patch could fail
A module Worker may fail to instantiate or load its ES module dependencies, giving the browser-level `Module failed to load` error before a Python exception can be reported.

## What changed
- Uses a same-origin **classic** `Worker` with `importScripts(pyodide.js)` rather than a module Worker with dynamic `import(pyodide.mjs)`.
- `importScripts` happens inside `try/catch`, allowing the website to display the actual CDN download exception.
- Sends an immediate `ready` event so the UI can distinguish worker-script startup failures from Python download failures.
- Cache-busts the worker URL and updates README troubleshooting.
- Preserves existing assignment UI and the A1 tests.

## Limitations
- Pyodide downloads still require network access to cdn.jsdelivr.net; if blocked, use another network or self-host runtime assets.
- Classic Workers have the same-origin security limitations as the previous module Worker. This is not a hardened untrusted-code sandbox.
- Full CDN-based execution could not be verified in this restricted environment.
