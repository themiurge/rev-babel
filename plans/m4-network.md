# Milestone 4 — network setup

**Goal.** The teacher's phone microphone reaches the server from anywhere,
and the caption stream reaches a browser in the classroom. Everything
before this milestone runs on one machine; this is where the system
becomes reachable.

**Domain: done.** `emiliovicari.com` is registered at Cloudflare
Registrar (5 September 2026), which puts the zone on Cloudflare
nameservers as part of registration — so the step with the propagation
delay is already behind us. The hostnames are settled:

| Hostname | Serves | Protected |
|----------|--------|-----------|
| `rev-babel.emiliovicari.com` | student caption pages | unguessable lesson id only |
| `mic.emiliovicari.com` | the teacher's capture page | yes — it opens a microphone |

Two names rather than one path prefix, so the capture host can sit behind
Cloudflare Access while the caption host stays open to a classroom machine
with no credentials to type (which is the whole premise of ADR 0010).

Recurring cost is the domain alone, ~$10.44/year at Cloudflare's at-cost
pricing. Tunnel, DNS, Universal SSL, WebSockets and Zero Trust Access for
under fifty users are all on the free tier. The remaining external steps
are in "What is needed from you" below.

## A fork to settle first: how audio gets in

Two paths, and the plan should not pretend they are the same one.

**Path A — phone browser tab (ADR 0004, as recorded).** A page on the
teacher's phone captures the lavalier through `getUserMedia`, encodes, and
streams over a WebSocket through the Cloudflare Tunnel. Needs HTTPS, which
the tunnel supplies; needs a Screen Wake Lock, which ADR 0004 already
anticipates; needs reconnect-on-drop logic.

**Path B — null sink on the server (as you described it).** The phone
streams audio to a `module-null-sink` on the server, and `DeviceSource`
reads the sink's monitor. Almost no code: M3's `DeviceSource` already
does the reading.

The catch is transport. A Cloudflare Tunnel carries HTTP and WebSockets,
not the RTP/UDP that phone audio-streaming apps speak. Path B over the
internet therefore needs a different link — WireGuard or Tailscale between
phone and server — which is a second remote-access mechanism alongside the
tunnel, and amends the premise of ADR 0003.

**Recommendation.** Build both, because M3's `AudioSource` abstraction
makes it cheap, and use them for different things:

- **Path B for rehearsal and local testing.** Same room, same LAN, zero
  browser work, working audio in an afternoon. This is what de-risks
  lesson 1.
- **Path A for the classroom**, over the tunnel, because it needs no app
  installed on the phone, no VPN on the phone, and no second ingress into
  the home network.

If Path A proves unreliable on the actual phone, falling back to Path B +
Tailscale in the classroom is a real option — but it is a decision with
consequences for `docs/architecture.md`, so record it. → *ADR 0016: the
audio ingress path, and what happens to ADR 0003/0004 if Path B wins.*

## The output leg

`apps/web` gains just enough to serve captions: a WebSocket endpoint that
subscribes to a lesson's caption stream and a page that renders it. The M3
console becomes a second subscriber to the same stream rather than a
separate code path — one publisher, several subscribers, which is what M5
then builds accounts and history on top of.

For lesson 1 this can be one URL per language —
`https://rev-babel.emiliovicari.com/lesson/<id>/captions?lang=ar` — with an
unguessable lesson id and no picker. That is the cut line from
[`README.md`](README.md).

## Security note, worth stating plainly

The capture endpoint opens a microphone in a room full of people who did
not consent to being recorded by strangers. It must not be reachable by
guessing a URL. Put the teacher's capture page behind Cloudflare Access
(email one-time PIN to the teacher's address is enough) or a bearer token
in the URL that is rotated per lesson. The student-facing caption pages
carry no microphone and can stay behind an unguessable path.

## Steps

1. `cloudflared` installed in WSL2; tunnel created; credentials stored
   outside the repository (`docs/data-and-privacy.md`). Step-by-step in
   [`infra/tunnel/README.md`](../infra/tunnel/README.md), including a
   smoke test that proves DNS, TLS and the tunnel before `apps/web`
   exists.
2. DNS records for the chosen hostnames; HTTPS verified from a phone on
   cellular data, not just from the LAN.
3. `apps/web`: caption WebSocket endpoint + a minimal page; the M3
   pipeline publishes into it.
4. Path B: `module-null-sink` on the server, a phone streaming to it over
   the LAN, `DeviceSource` reading the monitor. Rehearse with this.
5. Path A: capture page, WebSocket audio ingress, Wake Lock, reconnect
   with backoff, `WebSocketSource` feeding the pipeline.
6. Access control on the capture endpoint.
7. A 90-minute soak: phone streaming, captions rendering, tunnel restarted
   mid-run to prove recovery.

## What is needed from you (external, cannot be scripted)

- [x] **Register a domain** — `emiliovicari.com`, Cloudflare Registrar,
      5 September 2026.
- [x] **Cloudflare account and nameservers** — done by registering at
      Cloudflare, which requires its own nameservers and creates the zone.
- [x] **Hostname scheme** — `rev-babel.emiliovicari.com` for students,
      `mic.emiliovicari.com` for the capture page.
- [ ] **Create the tunnel** and route both hostnames to it
      (`cloudflared tunnel route dns <name> rev-babel.emiliovicari.com`,
      and again for `mic.`). Note where the credentials file lives on the
      server — not in the repo, and not in `data/` if `data/` is ever
      copied around. Its path goes in `.env` as `CF_TUNNEL_CREDENTIALS`;
      the file itself never does.
- [ ] **Cloudflare Access on `mic.emiliovicari.com`** — decide yes/no,
      and if yes, which email address receives the one-time PIN. Free for
      a single seat. Leave `rev-babel.emiliovicari.com` open, since a
      student cannot be asked to read an email and type a code.
- [ ] **Check the classroom network** before lesson 1: does its wifi or
      firewall allow WebSockets to `rev-babel.emiliovicari.com`? Some
      institutional networks do not. Test from the actual room, on the
      actual machines, ideally the week before.
- [ ] **Phone side**: which phone, whether the lavalier pairs and stays
      paired for 90 minutes, and whether the phone can be on power during
      the lesson.
- [ ] **Server side**: WSL2 starts on boot, Windows sleep and fast-startup
      disabled, and the desktop does not suspend at 17:00 mid-lesson.
      This is a quiet, extremely plausible way to lose a lesson.

## Acceptance criteria

- From a phone on cellular, open the capture page, speak, and see captions
  appear on a laptop on a different network, within the M3 latency budget
  plus tunnel round-trip.
- 90 minutes continuous, no manual intervention.
- Phone screen locked with Wake Lock held: capture continues. Phone
  backgrounded deliberately: the failure is detected and surfaced to the
  teacher, not silent.
- `cloudflared` restarted mid-session: clients reconnect on their own.
- The capture endpoint is unreachable without credentials.

## Risks

- **The classroom network is the one thing that cannot be tested from
  home.** Everything else on this list can be rehearsed; this cannot.
  Treat an on-site test as a scheduled task, not a hope.
- **Phone browser tab reliability** over 90 minutes is the known weak
  point already recorded in ADR 0004 and `docs/operations.md`. Path B
  exists partly as insurance against it.
