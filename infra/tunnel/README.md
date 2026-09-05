# infra/tunnel

Cloudflare Tunnel configuration for exposing the web app without forwarding
ports on the home router — see
[ADR 0003](../../docs/decisions/0003-cloudflare-tunnel.md).

## Hostnames

| Hostname | Serves |
|----------|--------|
| `rev-babel.emiliovicari.com` | student caption pages, open to the classroom |
| `mic.emiliovicari.com` | the teacher's capture page, protected |

Both are CNAMEs to the same tunnel, created with
`cloudflared tunnel route dns`. They are separate names so that the one
which opens a microphone can be put behind Cloudflare Access while the one
students use stays free of anything to type.

## Status

Placeholder. The domain is registered and the names are chosen; no tunnel
configuration exists yet. TODO: create the tunnel, route both hostnames to
it, and route it to `apps/web`. Credentials are referenced from `.env` by
path and are never committed — see `docs/data-and-privacy.md`.
