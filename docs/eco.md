# Eco

The lecture-captioning module. As designed; nothing below is implemented
yet — see `services/asr/README.md` and `services/mt/README.md` for current
(placeholder) status.

## Pipeline

1. **Capture** — audio streamed from the teacher's phone browser
   ([ADR 0004](decisions/0004-phone-as-microphone.md)).
2. **Voice activity segmentation** — audio is buffered and cut into segments
   on a voice-activity pause, rather than transcribed as a continuous
   stream. Streaming transcription visibly rewrites itself as more audio
   arrives, which is confusing on a caption screen. Segment-level
   transcription gives stable text at roughly 2–3 seconds of latency
   ([ADR 0005](decisions/0005-segment-level-transcription.md)).
3. **Speaker gating** — only the teacher is transcribed. The teaching
   assistant and students are not captioned by Eco.
   TODO: the exact gating mechanism (e.g. a single known audio source vs.
   voice-based gating) is not yet decided.
4. **Language identification** — the teacher speaks primarily Italian,
   occasionally English; the pipeline identifies which per segment before
   translation.
5. **Translation fan-out** — each transcribed segment is translated once
   per distinct student language present in the lesson (not once per
   student), using a dedicated translation model
   ([ADR 0006](decisions/0006-dedicated-translation-model.md)).
6. **Delivery** — translated captions are pushed to each student's browser
   over WebSocket, paired with the original Italian
   ([ADR 0008](decisions/0008-bilingual-caption-display.md)). The screen
   keeps a scrollback of recent segments so a student who stepped out of the
   room can catch up ([ADR 0009](decisions/0009-catch-up-buffer.md)).

## Failure behaviour

If translation fails for a segment or a language, that student's screen
falls back to Italian-only rather than showing nothing — see
`operations.md` for the full set of degradation rules.

## Unbuilt

Everything above is a design, not an implementation. `services/asr`,
`services/mt`, and the WebSocket fan-out in `apps/web` are all placeholders
at this stage (module docstrings only, no logic).
