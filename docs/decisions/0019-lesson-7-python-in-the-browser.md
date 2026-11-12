# 0019. Lesson 7: Python in the browser, and a coding assistant on the tutor's backend

- **Status:** accepted
- **Date:** 2026-11-12

## Context

Lesson 7 is a first taste of programming: in 90 minutes, an adult
beginner should make the computer do something she decided, in Python,
with an AI assistant to explain errors and suggest the next step. For
example, a student changes `range(3)` to `range(10)`, presses ▶ Esegui and
sees ten greetings; she mistypes `Print`, and the page tells her in
Italian that Python does not know «Print» and probably meant «print».

So the course needs to run code that students type. The app runs on the
maintainer's home desktop and is reachable from the internet. Until now no
page executed student input as code anywhere.

The lesson 6 tutor ([ADR 0018](0018-lesson-6-tutor-chatbot.md)) already
sends student text to Anthropic under a personal-data filter, caps, rate
limits and a nothing-stored rule. An assistant for code would send
students' code the same way.

## Decision

**Python runs in the student's browser, never on the server.** The page
loads Pyodide 314.0.7 (CPython 3.14 compiled to WebAssembly) in a Web
Worker. Server-side execution was rejected: making arbitrary code safe on
a home machine exposed to the internet needs a real sandbox, which this
project does not have and should not build for one lesson. A home-made
mini-interpreter was rejected because it would teach a dialect, with our
error messages instead of Python's, and could not be tested on this
machine.

**Pyodide is served by the app, not by a CDN, and not committed.** The
five core files (about 13.5 MB) are downloaded by
`scripts/fetch-pyodide.py` from the pinned GitHub release, checked against
committed SHA-256 sums, and kept in a gitignored
`apps/web/static/vendor/pyodide/` beside its MPL-2.0 licence. No request
goes to a third party at class time, and the repository does not grow by
13.5 MB of binaries (its large-file hook stays meaningful).

**The runner is one pure-Python file, tested under CPython.**
`static/lessons/lezione-7/python/runner.py` runs her program with a short
list of builtins, imports limited to `random` and `math`, a line-step
budget that stops endless loops, an output cap, a recursion cap, forgiving
normalisation of curly quotes and tabs, Italian explanations of the common
errors, and each step's success check. `input()` is answered from a list:
when it runs out the page asks her and re-runs the program with the same
random seed. Because Pyodide 314 is the same Python as the repository's
test environment, the test suite exercises what students get. A worker
that does not answer in 8 seconds is terminated and restarted. These
fences keep a beginner's program focused; they are not a security
boundary, since the code runs in her own browser tab.

**Running code sends nothing.** Her program, its output and her answers to
`input()` stay in the page's memory: no network call, no cookie, no
`localStorage`. Closing the tab ends them.

**The assistant reuses the tutor's backend.** `rev_babel_web/python_helper.py`
calls `tutor.call_model` (the same `claude-sonnet-5-5`, key and settings),
`tutor.looks_sensitive` and `tutor.limiter` (one shared budget for lessons 6
and 7). Only when she presses an assistant button do the step, the button,
her question (≤ 200 characters), her code (≤ 2,000) and the last error line
(≤ 400) go to the server and on to Anthropic. The program's output and her
`input()` answers are never sent. Each request stands alone (no history).
The filter runs on all of it, server-side; a match is never sent. The
static system prompt (prompt-cached) keeps replies short, in simple
Italian, limited to today's Python, ending with a "💡" line on asking well
or checking, and never writing the whole program; the server also cuts any
code block in a reply to 5 lines. Without a key, or on any failure, the
assistant answers from scripted advice per step and button.

**Nothing is stored.** Not on disk, not in the database, not in a log line
(a failed call logs the exception type only). The page keeps the last
three answers of the current step in memory.

## Consequences

Students' code, and the questions they type to the assistant, now go to
Anthropic when they press its buttons, under the same terms and
mitigations as the lesson 6 tutor. Code can contain things the filter
does not recognise (a name in a greeting, a street); the page says "use
invented names in the code" next to the button, and the prompt tells the
model not to repeat personal data, but it has been sent.

Easier: real Python with zero installation, working offline from the
internet once loaded, most of it tested here. Harder: a 13.5 MB first
load per student on the classroom network (the deck's first slide has
everyone open the page early), a setup step on any fresh checkout (`make
pyodide`), and a dependency on reasonably modern browsers (Web Workers
with dynamic `import()`).

Not verified at the time of writing: Pyodide loading and running in a real
browser (this machine has none), the classroom download time, whether
Cloudflare compresses or caches `.wasm`, and the assistant against the
real API.
