"""Tunnel and phone-capture smoke test. A verified blueprint, not project code.

Used on 2026-09-05 to prove the network layer before any of Eco existed; see
`scratchpad/README.md` for what it established and `plans/m4-network.md` for
the measurements it produced. Kept because the real capture page in
`apps/web` should be built from a shape already known to work end to end.

Proves, from a browser anywhere on the internet:
  - the tunnel reaches this machine at all
  - which hostname Cloudflare forwarded (caption host vs capture host)
  - that WebSockets survive the tunnel, with live round-trip latency
  - that a phone browser can stream microphone audio in, gated by a token

Run it with:

    uv run --with fastapi --with 'uvicorn[standard]' \
      uvicorn tunnel_smoke_server:app --host 127.0.0.1 --port 8000

It prints the URLs to open, including a freshly generated capture token.
Recordings are written to `data/recordings/`, which is gitignored: audio
never enters this repository (see `docs/data-and-privacy.md`).
"""

import asyncio
import json
import os
import pathlib
import secrets
import sys
import time
from datetime import datetime, timezone

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

sys.stdout.reconfigure(line_buffering=True)

app = FastAPI()
STARTED = time.time()

HERE = pathlib.Path(__file__).parent
REPO = HERE.parent

# Audio lands in the gitignored data directory, never beside the source.
CAPTURES = pathlib.Path(os.environ.get("CAPTURE_DIR", REPO / "data" / "recordings"))
CAPTURES.mkdir(parents=True, exist_ok=True)

# Hostnames match .env.example; override per environment rather than editing.
CAPTION_HOST = os.environ.get("ECO_PUBLIC_HOST", "rev-babel.emiliovicari.com")
MIC_HOST = os.environ.get("ECO_CAPTURE_HOST", "mic.emiliovicari.com")

# A fresh token per run unless one is supplied. Never commit a token: it is
# the only thing standing in front of an endpoint that records a room.
TOKEN = os.environ.get("CAPTURE_TOKEN") or secrets.token_urlsafe(9)

EXT = {"webm": ".webm", "ogg": ".ogg", "mp4": ".mp4"}

print(f"\n  capture page   https://{MIC_HOST}/?t={TOKEN}")
print(f"  caption check  https://{CAPTION_HOST}/")
print(f"  recordings     {CAPTURES}\n", flush=True)

PAGE = """<!doctype html>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>rev-babel tunnel check</title>
<style>
  :root { color-scheme: light dark; }
  body { font: 16px/1.5 system-ui, sans-serif; margin: 0; padding: 2rem 1.25rem;
         max-width: 34rem; margin-inline: auto; }
  h1 { font-size: 1.25rem; margin: 0 0 1.5rem; }
  .card { border: 1px solid #8883; border-radius: 10px; padding: 1rem 1.25rem;
          margin-bottom: 1rem; }
  .big { font-size: 1.5rem; font-weight: 600; }
  .ok { color: #0a7d32; } .bad { color: #b3261e; } .wait { color: #8a6d00; }
  dl { display: grid; grid-template-columns: auto 1fr; gap: .35rem .85rem; margin: 0; }
  dt { color: #8889; } dd { margin: 0; font-family: ui-monospace, monospace;
       overflow-wrap: anywhere; }
  #log { font-family: ui-monospace, monospace; font-size: .8rem; white-space: pre-wrap;
         max-height: 9rem; overflow-y: auto; color: #8889; }
</style>
<h1>rev-babel — tunnel check</h1>

<div class="card">
  <div>HTTPS through the tunnel</div>
  <div class="big ok">reached this machine</div>
</div>

<div class="card">
  <div>WebSocket through the tunnel</div>
  <div class="big wait" id="ws-state">connecting…</div>
  <div id="ws-detail"></div>
</div>

<div class="card">
  <dl>
    <dt>Host</dt><dd>__HOST__</dd>
    <dt>role</dt><dd>__ROLE__</dd>
    <dt>your IP</dt><dd>__IP__</dd>
    <dt>server time</dt><dd>__NOW__</dd>
  </dl>
</div>

<div class="card"><div id="log">…</div></div>

<script>
const state = document.getElementById('ws-state');
const detail = document.getElementById('ws-detail');
const log = document.getElementById('log');
let lines = [], sent = 0, echoed = 0, rtts = [];
function say(m) {
  lines.push(new Date().toLocaleTimeString() + '  ' + m);
  log.textContent = lines.slice(-40).join('\\n');
  log.scrollTop = log.scrollHeight;
}
const url = (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws';
say('opening ' + url);
const ws = new WebSocket(url);
ws.onopen = () => {
  state.textContent = 'open'; state.className = 'big ok';
  say('open — sending a ping every 2s');
  setInterval(() => { sent++; ws.send(JSON.stringify({t: Date.now()})); }, 2000);
  ws.send(JSON.stringify({t: Date.now()})); sent++;
};
ws.onmessage = (e) => {
  const d = JSON.parse(e.data); echoed++;
  const rtt = Date.now() - d.t; rtts.push(rtt);
  const med = [...rtts].sort((a,b)=>a-b)[Math.floor(rtts.length/2)];
  detail.textContent = echoed + ' echoed / ' + sent + ' sent · round trip ' + rtt
                     + ' ms (median ' + med + ' ms)';
  say('echo ' + rtt + ' ms');
};
ws.onerror = () => { state.textContent = 'error'; state.className = 'big bad'; say('error'); };
ws.onclose = (e) => {
  state.textContent = 'closed'; state.className = 'big bad';
  say('closed code=' + e.code + ' reason=' + (e.reason || '(none)'));
};
</script>
"""


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    host = request.headers.get("host", "(none)")
    # Host-based routing, exactly as the real app will do it: the capture
    # page is only ever served on the capture hostname.
    if host.split(":")[0] == MIC_HOST:
        return HTMLResponse((HERE / "capture.html").read_text())
    role = {
        CAPTION_HOST: "caption host — students",
        MIC_HOST: "capture host — teacher, should be protected",
    }.get(host.split(":")[0], "unrecognised hostname")
    return (
        PAGE.replace("__HOST__", host)
        .replace("__ROLE__", role)
        .replace("__IP__", request.headers.get("cf-connecting-ip") or "(not via Cloudflare)")
        .replace("__NOW__", datetime.now(timezone.utc).strftime("%H:%M:%S UTC"))
    )


@app.get("/healthz")
async def healthz():
    return JSONResponse({"ok": True, "uptime_s": round(time.time() - STARTED, 1)})


@app.websocket("/ws")
async def ws_echo(ws: WebSocket):
    await ws.accept()
    print(f"[ws] open  host={ws.headers.get('host')} ip={ws.headers.get('cf-connecting-ip')}")
    try:
        while True:
            await ws.send_text(await ws.receive_text())
    except (WebSocketDisconnect, asyncio.CancelledError):
        print("[ws] close")


@app.websocket("/audio")
async def audio_ingest(ws: WebSocket):
    if ws.query_params.get("t") != TOKEN:
        await ws.close(code=4401, reason="bad token")
        print("[audio] REJECTED — bad or missing token")
        return
    await ws.accept()

    stamp = datetime.now().strftime("%H%M%S")
    meta, path, fh = None, None, None
    chunks = bytes_in = 0
    started = last = time.monotonic()
    gaps = []

    try:
        while True:
            msg = await ws.receive()
            if msg["type"] == "websocket.disconnect":
                break
            if (text := msg.get("text")) is not None:
                meta = json.loads(text)
                mime = (meta.get("mime") or "audio/webm").split(";")[0]
                path = CAPTURES / f"capture-{stamp}{EXT.get(mime.split('/')[-1], '.bin')}"
                fh = path.open("wb")
                print(
                    f"[audio] open  mime={meta.get('mime')} "
                    f"sr={meta.get('sampleRate')} mic={meta.get('label')!r}"
                )
                print(f"[audio] ua={meta.get('ua')}")
                print(f"[audio] writing {path.name}")
                continue
            if (blob := msg.get("bytes")) is not None:
                now = time.monotonic()
                if chunks:
                    gaps.append(now - last)
                last = now
                chunks += 1
                bytes_in += len(blob)
                if fh:
                    fh.write(blob)
                    fh.flush()
                if chunks % 20 == 0:
                    secs = now - started
                    print(
                        f"[audio] {chunks} chunks · {bytes_in/1024:.1f} KiB · "
                        f"{bytes_in*8/secs/1000:.1f} kbps · {secs:.0f}s"
                    )
    except (WebSocketDisconnect, asyncio.CancelledError, RuntimeError):
        pass
    finally:
        if fh:
            fh.close()
        secs = max(time.monotonic() - started, 0.001)
        gaps_sorted = sorted(gaps)
        med = gaps_sorted[len(gaps_sorted) // 2] if gaps_sorted else 0
        print(
            f"[audio] CLOSED {chunks} chunks · {bytes_in/1024:.1f} KiB · "
            f"{secs:.1f}s · {bytes_in*8/secs/1000:.1f} kbps · "
            f"chunk gap median {med*1000:.0f} ms max {max(gaps or [0])*1000:.0f} ms"
        )
        if path:
            print(f"[audio] saved {path}")


LISTEN = CAPTURES


@app.get("/listen", response_class=HTMLResponse)
async def listen_page(t: str = ""):
    if t != TOKEN:
        return HTMLResponse("<p>bad token</p>", status_code=403)
    files = sorted(LISTEN.glob("*.ogg")) + sorted(LISTEN.glob("*.webm"))
    rows = (
        "".join(
            f"<div class=card><div class=n>{f.name} — {f.stat().st_size/1024:.0f} KiB</div>"
            f"<audio controls preload=none style='width:100%' "
            f"src='/audio-file/{f.name}?t={t}'></audio></div>"
            for f in files
        )
        or "<p>no captures yet</p>"
    )
    return HTMLResponse(
        "<!doctype html><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width,initial-scale=1'>"
        "<title>rev-babel captures</title><style>"
        ":root{color-scheme:light dark}body{font:16px/1.5 system-ui,sans-serif;"
        "max-width:32rem;margin:auto;padding:1.5rem 1.25rem}"
        ".card{border:1px solid #8883;border-radius:10px;padding:.9rem 1.1rem;margin:1rem 0}"
        ".n{font-family:ui-monospace,monospace;font-size:.8rem;color:#8889;margin-bottom:.5rem}"
        "</style><h1 style='font-size:1.15rem'>captures</h1>" + rows
    )


@app.get("/audio-file/{name}")
async def audio_file(name: str, t: str = ""):
    f = (LISTEN / name).resolve()
    if t != TOKEN or f.parent != LISTEN.resolve() or not f.is_file():
        return JSONResponse({"error": "no"}, status_code=403)
    kind = "audio/ogg" if f.suffix == ".ogg" else "audio/webm"
    return FileResponse(f, media_type=kind)
