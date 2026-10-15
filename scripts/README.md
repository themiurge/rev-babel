# scripts

Operational scripts (e.g. one-off setup or maintenance tasks) that don't
belong inside a specific service or app.

- `run-web.sh` — starts the web app on loopback with the variables from
  `.env` (copy `.env.example` first). `cloudflared` is the only way in
  from outside.
