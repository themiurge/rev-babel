# scratchpad

Verified blueprints — throwaway code that was run against the real system,
kept because it establishes a shape known to work. This is not project
code and nothing imports it. When the equivalent lands properly in
`apps/web`, the blueprint here stays as the record of what was proven and
when.

Nothing here is on the test or lint path for the packages; it is
documentation that happens to run.

## `tunnel_smoke_server.py` + `capture_page.html`

The network layer, proved on **5 September 2026**, twelve days before
lesson 1 and before a line of Eco existed. A FastAPI app behind the
Cloudflare Tunnel, plus a phone capture page that streams microphone audio
to it.

```sh
uv run --with fastapi --with 'uvicorn[standard]' \
  uvicorn tunnel_smoke_server:app --host 127.0.0.1 --port 8000
```

It prints the URLs to open, with a freshly generated capture token.
Hostnames come from `ECO_PUBLIC_HOST` / `ECO_CAPTURE_HOST` (defaults match
`.env.example`); recordings are written to `data/recordings/`, which is
gitignored — audio never enters this repository, per
[`docs/data-and-privacy.md`](../docs/data-and-privacy.md).

### What it established

- **HTTPS through the tunnel** on both hostnames, with the `Host` header
  intact — so one app on one port can separate caption traffic from
  capture traffic, which is what the two-hostname split depends on.
- **`CF-Connecting-IP` preserved**, so the app can tell classroom machines
  apart later.
- **WebSockets open and hold** through the tunnel. This was the result
  that could have invalidated the design outright.
- **Token-gated ingest**: a missing or wrong token is refused at the
  handshake (403), the right one upgrades (101). The `CAPTURE_TOKEN`
  pattern in `.env.example` is tested, not theoretical.
- **A phone browser can capture and stream** the microphone in 500 ms
  chunks over `wss://`, with a Screen Wake Lock held
  ([ADR 0004](../docs/decisions/0004-phone-as-microphone.md)).
- **What the phone actually produces**: WebM/Opus, 48 kHz, mono, ~32 kbps
  — one clean ffmpeg path for the decode step in
  [`plans/m2-speech-to-text.md`](../plans/m2-speech-to-text.md).

Measurements and what they imply are recorded in
[`plans/m4-network.md`](../plans/m4-network.md).

### Shapes worth carrying into `apps/web`

- **Host-based routing.** The capture page is served only on the capture
  hostname; the caption host never sees it.
- **500 ms `MediaRecorder` chunks**, matching the send buffer the plan
  settled on — link jitter becomes bounded delay rather than a gap in the
  audio.
- **`echoCancellation` and `noiseSuppression` off, AGC on.** The first two
  are tuned for phone calls and remove speech detail an ASR model wants.
- **Token checked before `accept()`**, so an unauthorised socket is
  refused at the handshake rather than after.
- **Path containment on file serving** — resolve, then verify the parent
  directory, before returning anything from disk.

### Bugs found here, worth not repeating

- The Stop button was never rebound after starting, so pressing it started
  a *second* capture; six concurrent recordings resulted. The real page
  needs an explicit guard against starting while a capture is live.
- The level meter was scaled 3×, so it pegged at roughly a third of actual
  amplitude and looked like clipping when the audio measured clean (flat
  factor 0, three samples at full scale in 822,000). A meter that lies
  about levels is worse than no meter.
- `print()` from a non-tty is block-buffered, so the diagnostics that
  mattered appeared minutes late. Line-buffer stdout in anything whose log
  is being watched live.

## Recordings

Test audio from that session lives in `data/recordings/` — the
maintainer's own voice reading invented sentences, one take mixing Italian
and English. Gitignored, and the seed of the read-aloud evaluation corpus
that [`plans/m2-speech-to-text.md`](../plans/m2-speech-to-text.md) calls
for, since real lesson audio can never be used.
