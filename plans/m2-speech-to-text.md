# Milestone 2 — audio to text

**Goal.** `services/asr` turns an audio file into the `Segment` stream that
M1 already consumes. Pre-recorded input only; live capture is M3.

**Why this shape.** Working from files makes the whole thing reproducible:
the same file yields the same segments, so segmentation and transcription
changes can be diffed rather than argued about. The live path in M3 then
only has to replace where the samples come from.

## The pipeline

1. **Decode.** Any container (`wav`, `mp3`, `m4a`, `ogg`, `webm`) through
   ffmpeg to 16 kHz mono float32. One entry point, so the phone's Opus and
   a test `.wav` take the same path.
2. **Voice activity detection.** Silero VAD (ONNX, CPU, small enough to
   keep off the GPU budget entirely). Starting parameters, to be tuned
   against real teaching pace: min speech 250 ms, min silence 500 ms,
   speech pad 200 ms, hard cut at 15 s.
3. **Speaker gate.** `docs/eco.md` leaves the mechanism open. For lesson 1
   the honest answer is the cheap one: the lavalier on the teacher is the
   only audio source, so the gate *is* the microphone. Voice-embedding
   gating is real work and is not on the critical path. → *needs a decision
   record: the audio source is the speaker gate* (issue 0011). Revisit if the lavalier turns out to
   pick up the room; note that `docs/data-and-privacy.md` requires
   incidental student audio to be discarded, which a single-source gate
   satisfies only as well as the microphone's pickup pattern does. Worth
   testing explicitly: speak from the back of a room while the lavalier is
   worn at the front, and check what comes out.
4. **Transcription.** faster-whisper (CTranslate2) on the GPU. Benchmark
   `medium`, `large-v3`-class, and a distilled variant at `int8_float16`
   and `float16`, for WER against latency and VRAM. Seed the decoder with
   a short Italian prompt of course vocabulary ("browser, cartella, doppio
   clic, salvare") so the domain words come out right.
5. **Language identification.** Per segment, from the ASR's own detection.
   Low confidence, or a segment where detection disagrees with the
   dominant language, is labelled `mixed` — which is exactly the signal M1
   Backend B needs.
6. **Emit.** `Segment` JSONL, gapless `seq`, timestamps relative to the
   start of the file.

## Steps

1. Decode + VAD + segment assembly, with the `Segment` validator from M1
   asserting the output. No model yet — a `null` ASR backend emits empty
   text, so segmentation can be tested and tuned in CI without a GPU.
2. faster-whisper backend behind an `Transcriber` protocol; model choice
   configured, not hard-coded.
3. Benchmark harness: WER, real-time factor, VRAM, cold start. → *needs a
   decision record: the transcription model and quantisation* (issue 0010).
4. Language identification and the `mixed` label.
5. `rev-babel-asr transcribe FILE > segments.jsonl`, plus `--vad-only` (to
   inspect segmentation without transcribing) and `--bench`.

## Evaluation without real transcripts

`docs/data-and-privacy.md` forbids real lesson audio or transcripts
anywhere near this repository, which rules out the obvious test set. Two
substitutes, both compliant:

- **Public Italian speech** (Common Voice Italian, VoxPopuli Italian) with
  its own references, downloaded into gitignored `data/eval/`. Gives a WER
  number comparable to published ones, on speech that is nothing like a
  classroom.
- **A read-aloud of the invented classroom corpus from M1**, recorded by
  the maintainer, through the actual lavalier, in a room. This is the
  maintainer's own voice reading fictional sentences — no student is
  involved — and the audio stays gitignored (`*.wav` already is). It is
  the only measurement that reflects the real microphone, the real
  vocabulary, and the real acoustics.

Record both numbers. The second is the one to trust.

## Acceptance criteria

- A 10-minute file processes at real-time factor < 0.3 end to end
  (decode + VAD + transcribe), on the 4080 SUPER, model resident.
- No segment exceeds 15 s; no segment boundary falls inside a word on the
  read-aloud corpus.
- WER on the read-aloud corpus recorded in the decision record, with the failure
  cases listed rather than averaged away.
- Same file in twice → byte-identical segments out.
- `make test` passes CPU-only, with the `null` backend.
- `rev-babel-asr transcribe x.wav | rev-babel-mt --targets en,fr,ar`
  works as a shell pipeline. This is M3's whole thesis, proved a day early
  and for free.

## Risks

- **Teaching pace defeats the VAD.** A teacher explaining something rarely
  pauses cleanly for 500 ms. If segments run long, latency grows past the
  2–3 s ADR 0005 promises; if the silence threshold drops, segments
  fragment mid-thought and translation quality falls. Tune on the
  read-aloud recording, but expect to retune after lesson 1.
- **Classroom noise.** Five students, young children possibly present. The
  lavalier's pickup is the whole speaker gate, so this is a hardware
  question as much as a software one — test it before buying nothing else.
