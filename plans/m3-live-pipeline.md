# Milestone 3 — live pipeline to the console

**Goal.** Audio arriving continuously → segments → translations → printed
to a terminal as they are ready, with latency measured at every stage. No
browser, no network. This is the milestone where Eco first exists as a
system rather than as two programs.

**Why a console first.** The console is not a throwaway. It stays as the
teacher-side debug view for the rest of the project: when a student says
the captions stopped, the console is where you look. Building it now also
means the browser work in M4/M5 is only a rendering problem, because the
stream behind it is already proven.

## Shape

An `AudioSource` protocol with three implementations, chosen by config:

- `FileSource` — replays a file in real time (not as fast as possible),
  so the live path can be exercised deterministically and without a
  microphone. This is what the tests use.
- `DeviceSource` — reads a named PipeWire/PulseAudio source. This is what
  reads the null sink in M4, and what reads a USB mic today.
- `WebSocketSource` — added in M4, when there is a socket to read from.

Behind it, one asyncio pipeline with bounded queues:

```
source → ring buffer → VAD segmenter → [ASR worker] → [MT worker] → sinks
```

Bounded, because the interesting question is not what happens when it
keeps up but what happens when it does not. Policy, to be implemented
explicitly rather than emerging from queue behaviour:

- Audio is never dropped between source and segmenter — a gap in the audio
  is a gap in the lesson.
- If the ASR queue backs up, log it loudly; the segmenter keeps producing.
- If the MT queue backs up, shed *per language*, oldest first, emitting
  `degraded=True` captions rather than falling further behind. A student
  reading Italian and a two-second-late French line is better served than
  one reading a translation of what was said a minute ago.

Sinks are pluggable from the start: the console renderer is one, the
metrics writer is another, and M5's WebSocket fan-out becomes a third
without touching the pipeline.

## The console renderer

- The Italian line, then one line per target language, in a stable order.
- A latency badge per segment (speech end → caption printed), so
  regressions are visible while working rather than in a benchmark.
- Arabic on its own line. Bidirectional text in a terminal is unreliable
  and terminal-specific; do not spend time fighting it here, because the
  browser is where it has to be right (M5).
- `--metrics run.jsonl` writes per-stage timings for later analysis.

## Retention — a decision this milestone forces

The moment the pipeline runs live it produces a transcript of the
teacher's speech, and `docs/data-and-privacy.md` records the retention
period as undecided. It cannot stay undecided once the thing runs.

Proposed default, to be confirmed and recorded: run logs are written to
gitignored `data/runs/<lesson_id>/` and deleted when the process exits,
unless `--keep` is passed for a session being debugged. Nothing is
retained by default; retention becomes opt-in and deliberate. → *ADR 0014:
Eco transcript retention.* Whatever is decided, update
`docs/data-and-privacy.md` and remove the TODO rather than leaving both.

## Steps

1. `AudioSource` protocol; `FileSource` with real-time pacing.
2. The async pipeline with bounded queues and the shedding policy above,
   plus tests that drive it into backlog on purpose and assert the policy
   holds.
3. Console renderer and the metrics sink.
4. `DeviceSource` against a local microphone.
5. Latency instrumentation end to end; a 20-minute run, numbers recorded.
6. Clean shutdown: Ctrl-C flushes in-flight segments and stops within a
   second, no orphaned GPU memory.

## Acceptance criteria

- 20-minute continuous run: p50 speech-end→console ≤ 3 s, p95 ≤ 5 s,
  matching what ADR 0005 promises.
- Memory flat across the run; queues bounded; no segment silently lost.
- Deliberate backlog (throttle the MT worker) sheds by the stated policy
  and recovers when the throttle lifts.
- Killing and restarting the MT backend mid-run produces `degraded`
  captions during the gap, not a crashed pipeline.
- The same file through `FileSource` twice yields the same segments.

## Risks

- **Latency compounds.** Each stage's budget is comfortable alone; the sum
  is the number that matters. Measure the sum from the first day of this
  milestone, not at the end.
- **GPU contention between ASR and MT** on one card, alternating small
  batches. If it shows up as jitter, the answer is to serialise them
  behind one worker rather than to over-engineer scheduling.
