# infra/tunnel

Cloudflare Tunnel configuration for exposing the web app without forwarding
ports on the home router — see
[ADR 0003](../../docs/decisions/0003-cloudflare-tunnel.md).

## Hostnames and origin service

The tunnel is **managed from the Cloudflare dashboard**, so its ingress
rules live in Cloudflare rather than in this repository. Both public
hostnames point at the same local app, which distinguishes them by `Host`
header:

| Public hostname | Type | URL | Serves |
|-----------------|------|-----|--------|
| `rev-babel.emiliovicari.com` | HTTP | `127.0.0.1:8000` | student caption pages, open to the classroom |
| `mic.emiliovicari.com` | HTTP | `127.0.0.1:8000` | the teacher's capture page, protected |

Two names rather than one path prefix, so that Cloudflare Access can
protect the host which opens a microphone while the host students use
stays free of anything to read or type (ADR 0010).

Two things about that URL that are easy to get wrong:

- **HTTP, not HTTPS.** TLS is terminated at Cloudflare's edge; the hop
  from `cloudflared` to the app never leaves the machine. Pointing at
  `https://` fails the origin handshake unless TLS verification is also
  disabled, which is complexity bought for nothing.
- **`127.0.0.1`, not `localhost`.** `localhost` may resolve to `::1`,
  and an app bound only to IPv4 then refuses a connection that looks, from
  the dashboard, like a tunnel fault.

WebSockets need no configuration — `cloudflared` proxies them by default,
which is what both the audio ingress and the caption fan-out depend on.

## The connector

The connector runs inside WSL2
([ADR 0002](../../docs/decisions/0002-run-everything-in-wsl2.md)),
installed with the token from the dashboard's connector command:

```sh
sudo cloudflared service install <TOKEN>
```

That token authenticates the tunnel. It is a secret: it belongs in the
systemd unit the installer writes, never in this repository, and never
pasted anywhere it might be logged (see
[`docs/data-and-privacy.md`](../../docs/data-and-privacy.md)).

Check it with `systemctl status cloudflared` and in the dashboard, where a
healthy tunnel shows its connector as active.

**WSL2 does not start on Windows boot by itself**, so a reboot takes the
tunnel down until something starts the guest — a real failure mode for a
lesson that begins at 16:30. Fixing it properly belongs with the rest of
the supervision decision in
[`plans/m6-end-to-end.md`](../../plans/m6-end-to-end.md).

## Smoke test, before any of the app exists

Worth doing the day the tunnel is created rather than the day the app is
ready: it proves DNS, TLS and the tunnel independently of any rev-babel
code, so that when something breaks later there is one fewer layer to
suspect.

```sh
python3 -m http.server 8000    # stands in for apps/web
```

Then open `https://rev-babel.emiliovicari.com` **from a phone on cellular
data**, not from the LAN — the point is to prove the path in from the
internet, and a phone on the house wifi may reach the machine without the
tunnel being involved at all.

A directory listing over valid HTTPS means ADR 0003 is proven end to end,
and milestone 4's remaining risk is entirely the classroom's network,
which cannot be tested from here.

## Status

Domain registered, tunnel created and managed from the dashboard, both
hostnames routed. `apps/web` does not exist yet, so `127.0.0.1:8000`
answers only when something is put there by hand.

## If this ever moves back into version control

`config.example.yml` is the same routing expressed as a locally-managed
tunnel: ingress rules in a file here, credentials in a JSON file
referenced by path. It is unused while the dashboard owns the tunnel, and
is kept because a config in version control is easier for a future reader
to audit than a dashboard nobody else can see. Switching would mean
recreating the tunnel with `cloudflared tunnel create`; the two management
modes are not interchangeable for one tunnel.
