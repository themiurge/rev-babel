# Milestone 1 — the translation module

**Goal.** `services/mt` consumes a stream of transcribed segments and emits
translated captions in English, French and Arabic. No audio, no network, no
browser. It runs from a file and to a file, so it can be evaluated,
benchmarked and regression-tested on its own.

**Why first.** It is the only part of Eco with no upstream dependency, and
it is the part whose quality we cannot assess by looking at it — Italian
into Arabic has to be measured, and measuring it needs a harness that
exists before there is a pipeline to plug it into.

## The input contract

Defined in `packages/contracts`, because `services/asr` (M2) produces it
and `apps/web` (M5) forwards it.

```python
class Segment:
    lesson_id: str      # opaque id, not derived from anything personal
    seq: int            # monotonic within a lesson, gapless
    started_at_ms: int  # milliseconds from lesson start
    ended_at_ms: int
    source_lang: str    # "it" | "en" | "mixed" | "und"
    text: str
```

```python
class Caption:
    lesson_id: str
    seq: int            # the Segment.seq this translates
    source_lang: str
    source_text: str    # carried through, so the client can show both (ADR 0008)
    target_lang: str    # "en" | "fr" | "ar" | ...
    text: str
    engine: str         # which backend produced it, for the record
    latency_ms: int
    degraded: bool      # true when translation failed and the client should show Italian only
```

Wire format is JSON Lines, one object per line, UTF-8. It is the same
format on stdin/stdout in M1 as it is on the asyncio queues in M3 and on
the WebSocket in M5 — one shape, three transports.

**Characteristics the producer must guarantee**, because the translator's
behaviour depends on them:

- Text is a committed segment, never a partial re-decode (ADR 0005).
- Ends on a sentence boundary or a voice-activity pause; no split words.
- Roughly 3–15 seconds of speech, hard-capped; a `seq` never repeats.
- Arrives in `seq` order. Out-of-order input is an error, not a case to
  handle silently.

M1 ships a validator that asserts these on the way in, so that when M2's
segmenter misbehaves the failure names itself.

## Steps

1. **Contracts and codec.** `Segment`, `Caption`, JSONL read/write, order
   and shape validation, tests. Pydantic v2, since `apps/web` will carry
   it anyway. → *ADR 0011: the segment/caption contract and its JSONL wire
   format.*
2. **Skeleton and CLI.** A `Translator` protocol
   (`translate(segment, targets) -> list[Caption]`), a bounded async
   queue, and `rev-babel-mt --targets en,fr,ar [--backend X] < in.jsonl >
   out.jsonl`. Ship an `echo` backend that returns the source text
   unchanged: it is what CI runs, and what the pipeline falls back to when
   every model is unavailable.
3. **Evaluation harness** — before any model. Two corpora:
   - *FLORES-200 devtest*, it→en/fr/ar, downloaded by a script into
     gitignored `data/eval/`. Public benchmark data, never committed.
   - *A classroom-register set*, ~60 invented sentences written by hand in
     the register of a computer-literacy lesson, of which ~15 are
     code-switched Italian/English ("fate doppio clic sul file, poi *save
     as*"). Invented, therefore committable — and the only corpus that
     actually resembles what Eco will see. It is the single highest-value
     artefact in this milestone.

   Metrics: chrF++ against reference, per-segment latency p50/p95 per
   language, VRAM resident, and cold-start time. Output a table the ADR
   can quote.
4. **Backend A — small and dedicated.** A CTranslate2-served
   encoder-decoder MT model (Opus-MT per-pair, or NLLB-200 distilled).
   Tiny, fast, and it proves the GPU plumbing. Whatever else wins, this
   stays as the low-cost fallback path.
5. **Backend B — an instruction-tuned LLM used solely for translation.**
   Two things Backend A structurally cannot do: handle a segment that
   mixes Italian and English without a per-segment language token, and use
   the previous segment or two as context so pronouns and continuations
   survive. A dedicated instance for translation still satisfies ADR 0006
   — that ADR separates translation from *Play's* chat model, not from all
   chat models. It costs more VRAM, which is the trade to measure.
6. **Glossary / term protection.** A small YAML list of Italian strings
   that must survive translation verbatim — the labels the student is
   looking at on her own screen. Translating *Salva con nome* into Arabic
   makes the caption describe a button she cannot find. Rendered in
   quotes, verified by a fixture.
7. **Choose and record.** Run the eval across backends and languages, pick
   the default, write the numbers down. → *ADR 0012: the translation model
   and why.*
8. **Cache and batch.** LRU on `(source_text, target_lang)` — teaching
   repeats itself, and "avete capito?" should not cost a forward pass
   every time. One segment × N languages goes in as one batch.
9. **Failure path.** Per-language timeout (start at 1.2 s). On timeout or
   error, emit `degraded=True` carrying the source text, never an
   exception and never a dropped caption — `docs/operations.md` promises
   the student sees Italian rather than nothing.

## Also evaluate: the languages we do not yet know we need

`docs/open-questions.md` records that a student's first language may be
Sorani or Kurmanji Kurdish, to be established in lesson 1 — two days
*after* the system must work. So make the target set configuration, not
code, and run the eval for `ckb` and `kmr` alongside en/fr/ar in step 7.
Knowing before 17 September whether either language is servable at
acceptable quality is worth the extra hour; discovering it live is not.

This does not answer the open question — it prepares for either answer.

## Acceptance criteria

- 100 invented segments in → 300 captions out, in `seq` order, none
  dropped, none duplicated.
- p95 fan-out latency ≤ 600 ms for three languages with the model
  resident, measured on the RTX 4080 SUPER.
- chrF++ recorded for it→{en,fr,ar} on both corpora, for every backend
  tried, and quoted in ADR 0012.
- Glossary fixture: protected terms preserved verbatim in 20/20 cases.
- Injected timeouts produce `degraded` captions; no exception escapes the
  translator.
- `make test` passes on a CPU-only runner with no model downloaded.

## Risks

- **Arabic quality cannot be verified in-house.** No Arabic reviewer is
  identified. Mitigation is structural rather than technical: ADR 0008
  keeps the Italian on screen, so a poor translation degrades to "read the
  Italian", and the teaching assistant remains the human fallback. Worth
  asking whether anyone in the provider's network can review 30 lines.
- **Code-switched segments** are the failure mode most likely to look fine
  in the benchmark and bad in the room. This is why the invented corpus
  carries a deliberate 25% code-switched share.
- **VRAM.** A larger translation model is the right answer for M1 and the
  wrong one once Play loads (`docs/architecture.md`). Record the measured
  footprint now so M6's shed policy has a number to work from.
