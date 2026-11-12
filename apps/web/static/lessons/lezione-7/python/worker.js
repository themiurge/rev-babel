/* Lesson 7: runs the student's Python with Pyodide, off the page's main
   thread, so an endless program can be stopped by terminating this worker.
   The program, its output and her answers never leave the browser. The
   logic is in runner.py (also tested under CPython); this file only loads
   Pyodide and passes JSON both ways. See docs/decisions/0019. */
"use strict";
let runner = null;

self.onmessage = async (event) => {
  const msg = event.data || {};
  if (msg.type === "boot") {
    try {
      importScripts(msg.pyodideUrl + "pyodide.js");
      const py = await loadPyodide({ indexURL: msg.pyodideUrl });
      const source = await (await fetch(msg.runnerUrl)).text();
      py.FS.mkdirTree("/home/pyodide");
      py.FS.writeFile("/home/pyodide/runner.py", source);
      py.runPython("import sys\nif '/home/pyodide' not in sys.path: sys.path.insert(0, '/home/pyodide')");
      runner = py.pyimport("runner");
      self.postMessage({ type: "ready" });
    } catch (err) {
      // The error's name only: nothing from the student is in play yet anyway.
      self.postMessage({ type: "boot-failed", detail: String((err && err.name) || "Error") });
    }
    return;
  }
  if (msg.type === "run") {
    try {
      const out = runner.run_json(msg.code, JSON.stringify(msg.answers || []), msg.seed, msg.step);
      self.postMessage({ type: "result", id: msg.id, result: JSON.parse(out) });
    } catch (err) {
      self.postMessage({ type: "crashed", id: msg.id });
    }
  }
};
