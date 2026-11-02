# apps/web/static

Static assets (CSS, client-side JS, images) served directly by the web app.
There is no frontend build step: files are served as authored.

- `style.css` - the site-wide stylesheet.
- `lessons/lezione-N/...` - per-lesson games and tutorial code.
  `lessons/guided-editor.js` is the shared engine behind the two lesson 5
  word-processor tutorials (the arrow, the step runner, the bilingual
  pane); each tutorial's own file only lists its steps.
  `lessons/lezione-6/tutor/tutor.js` is the lesson 6 tutor chatbot's page
  logic (missions, chat, the "Rispondi in" toggle); it keeps the
  conversation in memory only - no cookie, no `localStorage`.
- `vendor/quill/` - Quill 2.0.3 (BSD-3, licence alongside), copied in
  rather than loaded from a CDN so the classroom works offline. Update it
  by replacing the two files and re-running the tutorials end to end.
