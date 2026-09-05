# infra/tunnel

Cloudflare Tunnel configuration for exposing the web app without forwarding
ports on the home router — see
[ADR 0003](../../docs/decisions/0003-cloudflare-tunnel.md).

## Hostnames

| Hostname | Serves |
|----------|--------|
| `rev-babel.emiliovicari.com` | student caption pages, open to the classroom |
| `mic.emiliovicari.com` | the teacher's capture page, protected |

Both are CNAMEs to the same tunnel and both route to the same local app on
`127.0.0.1:8000`, which distinguishes them by `Host` header. They are
separate names so that the one which opens a microphone can be put behind
Cloudflare Access while the one students use stays free of anything to
type.

## Setting it up

Everything runs inside WSL2 ([ADR 0002](../../docs/decisions/0002-run-everything-in-wsl2.md)).
Steps 1 and 2 need a password and a browser respectively, so they are
yours to run; the rest is scriptable.

### 1. Install `cloudflared` (needs sudo)

```sh
sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg \
  | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt-get update && sudo apt-get install -y cloudflared
```

The apt repository rather than a downloaded `.deb`, because this daemon is
the single path in from the internet and should get security updates with
everything else on the machine.

### 2. Authenticate (needs a browser)

```sh
cloudflared tunnel login
```

It prints a URL. Open it in Windows, pick the `emiliovicari.com` zone, and
authorise. This writes `~/.cloudflared/cert.pem`, which is what lets the
next two steps create a tunnel and write DNS records. It is an account
credential: it stays in `~/.cloudflared/`, never in this repository.

### 3. Create the tunnel

```sh
cloudflared tunnel create rev-babel
```

Prints a UUID and writes `~/.cloudflared/<UUID>.json` — the tunnel's own
credentials. Also a secret, also never committed. Put its path in `.env`
as `CF_TUNNEL_CREDENTIALS`.

### 4. Point both hostnames at it

```sh
cloudflared tunnel route dns rev-babel rev-babel.emiliovicari.com
cloudflared tunnel route dns rev-babel mic.emiliovicari.com
```

Each creates a proxied CNAME in the `emiliovicari.com` zone. Verify with
`cloudflared tunnel list` and in the Cloudflare dashboard's DNS tab.

### 5. Write the config

```sh
cp infra/tunnel/config.example.yml infra/tunnel/config.yml
# then replace <TUNNEL-UUID> with the id from step 3
```

### 6. Run it

```sh
cloudflared tunnel --config infra/tunnel/config.yml run rev-babel
```

Foreground, for now. Running it as a systemd unit that survives a reboot
is part of milestone 6, where how the whole stack is supervised gets
decided — see [`plans/m6-end-to-end.md`](../../plans/m6-end-to-end.md).

## Smoke test, before any of the app exists

Worth doing the day the tunnel is created rather than the day the app is
ready: it proves DNS, TLS and the tunnel independently of any rev-babel
code, so that when something breaks later there is one fewer layer to
suspect.

```sh
# terminal 1 — stand in for apps/web
python3 -m http.server 8000

# terminal 2
cloudflared tunnel --config infra/tunnel/config.yml run rev-babel
```

Then open `https://rev-babel.emiliovicari.com` **from a phone on cellular
data**, not from the LAN — the point is to prove the path in from the
internet, and a phone on the house wifi may reach the machine without the
tunnel being involved at all.

You should get a directory listing over HTTPS with a valid certificate. If
you do, ADR 0003 is proven and milestone 4's remaining risk is entirely
the classroom's network, which cannot be tested from here.

## Status

Domain registered and hostnames chosen. The tunnel itself is not created
yet; follow the steps above. Credentials are referenced from `.env` by
path and are never committed — see
[`docs/data-and-privacy.md`](../../docs/data-and-privacy.md).
