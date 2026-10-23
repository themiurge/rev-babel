# scripts

Operational scripts (e.g. one-off setup or maintenance tasks) that don't
belong inside a specific service or app.

- `run-web.sh` — starts the web app on loopback with the variables from
  `.env` (copy `.env.example` first). `cloudflared` is the only way in
  from outside.
- `translate.py` — `scripts/translate.py --from it-IT --to en-US "testo"`
  calls the Google Cloud Translation API (key in `GOOGLE_TRANSLATE_API_KEY`).
  Course material only: the text is sent to Google.
