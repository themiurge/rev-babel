# Lezione 8: I social network

A plan for **several implementers working in parallel** plus a lead who
integrates. It says what to build, in what order, who owns which file, and
how we will know it works. The decisions it needs (a teacher-only
materials store outside git, presenter notes, a projector game) are
written out as ADR 0020 in section 10; the docs package commits that ADR.

**Lesson:** "I social network" - how social media work and how to use
them safely, for adult migrant women, 90 minutes, mixed reading fluency.
A second, shorter session for the parents in the group.

**Source:** the maintainer's research brief for this lesson (a design
brief for three artifacts, researched 2026-11-16, not in the repository). This plan follows the brief's content but **the
repository's way**: the two decks are local Slide Sync Lite decks
(ADR 0016), the game is a page served by the app, translations go through
`scripts/translate.py`'s Google route, and real media come from a
teacher-only **materials store** that lives in `data/`, never in git.
Per [`docs/data-and-privacy.md`](../docs/data-and-privacy.md), nothing
committed names the course provider, the venue, the city, the teacher or
the teaching assistant: "il corso", "gli operatori", "l'insegnante",
"the assistant".

**Status:** designed 2026-11-16. Nothing built yet.

**Calendar:** the course runs on Thursdays through 19 November. If lesson
8 is on Thursday 19 November there are **three days**: see the cut line
in section 12.4.

---

## 0. What everyone gets, in one paragraph

**The teacher**, on his phone, opens `mic.emiliovicari.com/materiali`:
one page, a card per thing the lesson needs ("Slide 11 - la home di
YouTube, account A", "Gioco I1 - una tua foto vera, senza volti"), each
with plain Italian instructions, safety notes, a big "📷 Tocca per
scegliere o fotografare" area, instant preview, and a progress line
("Gioco: 12 di 18 pronti"). Files are cleaned of GPS/EXIF and kept in
`data/materials/` on his machine. **In class**, `/present` shows the
35-page main deck "Social media: come funzionano e come usarli in
sicurezza"; each student follows it on `/follow`, Italian beside her own
language. Missing material shows as a clear "📦 Materiale in arrivo" box
or as a drawn example. Presenter notes (English, with dated "VERIFY"
flags) are never sent to students: the teacher sees them on his phone at
`/present/telecomando`, which is also a remote control. At slide 30 he
switches the projector to `/vero-o-falso`: six categories, 20 items,
teams vote with four coloured A4 cards (printed from
`/vero-o-falso/carte`), countdown, reveal with clue and action, scores
only at the end of each category. Students can open "Scheda da portare a
casa" from the lesson 8 page (A5, Italian plus their language) and the
teacher can print it. The parents' deck "Genitori e social media: come
accompagnare i figli" (14 slides) is a separate deck on `/present`.

---

## 1. Decisions taken here, with reasons

### 1.1 Languages

Italian is authored here, in full, and is enough to teach. The other five
languages (`en`, `fr`, `ckb`, `kmr`, `ar`) are filled by a **separate,
skippable package (WP-T, section 11)** that runs a new
`scripts/translate_content.py` on top of `scripts/translate.py`'s Google
Cloud Translation call (HTML mode, `translate="no"` respected, tag
signatures validated, unreviewed). Volume is about 25,000 Italian
characters, i.e. about 125,000 characters for five languages: inside
Google's monthly free tier, so cost is not the obstacle; only the key is.
If `GOOGLE_TRANSLATE_API_KEY` is not set, WP-T commits its script and
tests and the content ships Italian-only: the follow page already hides
the second pane when a slide has no translation (ADR 0016), and the game
and the take-home card simply offer fewer languages. The script also
exports and imports a CSV (`id,it,en,fr,ckb,kmr,ar`) for the maintainer's
spreadsheet workflow.

Presenter notes are in **English** (the brief's choice: the assistant can
read them). They are never translated and never sent to students.

Text the teacher types on the materials page (a caption, a link) is shown
as typed, in Italian, in every pane. It is not translated.

### 1.2 The materials store (the maintainer's key request)

- **Where:** `data/materials/<SLOT>/file.<ext>` plus
  `data/materials/<SLOT>/meta.json`, under the already-gitignored `data/`.
  `.gitignore` gets an explicit `data/materials/` line in the **first
  commit** of the build (privacy rule: extend `.gitignore` before anything
  writes there). Uploads stream to `data/materials/.tmp/` first.
- **What can be provided:** a committed **manifest**
  (`materials_manifest.json`, section 4.2) lists every slot: id, which
  artifact, where it appears, what to provide and how (plain Italian, to
  "tu"), safety notes, whether faces are forbidden, the game answer, and
  any written fields. Nothing else can be uploaded: unknown slot ids are
  404.
- **Who:** only the teacher-only capture host (`_require_capture_host`,
  as `/present`, ADR 0014). Because this is **write access to what
  students see**, the page also honours an optional `MATERIALS_KEY` from
  `.env`: when set, the page asks for it once (or takes it from a
  bookmarked `?k=` link) and remembers it in the session. When unset, the
  page shows a yellow note saying so. The risk is recorded in ADR 0020.
- **As easy as possible:** one mobile-first page; a card per slot; status
  badge (mancante / incompleto / pronto / saltato); a big drop zone that
  is also a `<label>` for a file input (on a phone: camera or gallery);
  drag and drop; paste a screenshot with Ctrl+V into the focused card or
  with a "📋 Incolla" button; instant preview; replace and delete; an
  in-page **🎙️ Registra** for audio slots; written fields that save on
  their own; "Salta questo materiale"; progress per artifact; a "Cosa
  manca" tab with "📋 Copia la lista". Ready cards fold to one line. No
  configuration.
- **Cleaning, with what is installed (no Pillow, no new dependency):**
  - in the browser, every image is decoded and **re-encoded through a
    canvas** (long side at most 2,000 px for photos, 2,400 for
    screenshots; JPEG 0.88 for photos, PNG for PNG screenshots). That
    drops all metadata (EXIF, GPS, XMP) and applies the photo's rotation;
  - on the server, `media_clean.py` (stdlib only) identifies the file by
    its first bytes and strips metadata format by format: JPEG APP1-APP15
    and COM segments (keeping JFIF, ICC profile, Adobe), PNG ancillary
    chunks such as `tEXt`/`iTXt`/`zTXt`/`eXIf`/`tIME`, WebP `EXIF`/`XMP `
    chunks, MP4/MOV/M4A `udta`/`meta`/`uuid` boxes (where phones put the
    location) overwritten in place as `free` boxes of zeros, MP3 ID3 tags,
    WAV `LIST` and other non-audio chunks. Ogg and WebM are accepted as
    they are (browser and messaging-app recordings carry no location).
    HEIC is refused with an explanation (the browser path converts it
    first on iPhones). Unknown types are refused.
  - caps: images 15 MB, audio 20 MB, video 90 MB (under Cloudflare's
    100 MB request limit), 2 GB for the whole store. The original file
    name is never stored.
- **Serving:** always on the capture host
  (`/admin/materials/<SLOT>/file`); to a logged-in student **only**
  through `/api/live/material/<SLOT>`, and only while the live local
  slide contains that slot and the session is live. Game media are
  served on the capture host only (the game runs on the projector).
- **Degrading:** a deck marks a material spot with
  `<rb-slot data-slot="S11-A"></rb-slot>`. The server replaces it with the
  image, video or audio when it exists; otherwise with the slot's own
  inner fallback (a drawn example labelled "Esempio creato per il corso")
  or, if empty, a clear "📦 Materiale in arrivo" box. A game item without
  its file uses its drawn example if it has one, otherwise it is skipped
  and flagged "📦" for the teacher.

### 1.3 The game "Vero o falso?" is driven by the teacher on the projector

The brief wants no shared-state software. Slide Sync Lite syncs one
integer for decks; extending it to game screens would be shared state.
So the game is **one page on the capture host** (`/vero-o-falso`),
driven only by the teacher, shown on the projector. Students vote with
paper cards. Students' `/follow` shows slide 30 ("Guardate lo schermo
grande") meanwhile. State is client-side, mirrored to the teacher
browser's `localStorage` (team names and points only, no student data)
so a reload resumes. On start it **preloads every media file into
memory**, so a network blip mid-game does not break it. Scoring is
computed by a Python function and shipped to the page as a per-item
points table (tested), so the JavaScript only adds numbers.

> Fork for the maintainer: ADR 0014 was written for a room **without** a
> projector; the brief says there is one. If there is none on the day,
> the game needs the teacher's screen to be visible to the class (or a
> later "mirror to /follow" feature, not designed here).

### 1.4 Presenter notes stay with the teacher

A slide in a deck JSON may now carry, beside its language keys,
`"id"` (`"S11"`), `"notes"` (English), `"verify"` (a list of dated
"VERIFY before class" flags) and `"optional": true`. `decks.get_slide`
never returns them, so `/api/live/slide` (students) cannot leak them.
`/admin/api/decks/<slug>/slides/<n>` (capture host) returns them plus
which materials are missing. `/present` keeps notes **hidden by default**
(the projector shows that page) behind a "Note (N)" toggle, and
`/present/telecomando` is a phone page with the notes, the flags, the
missing materials and big ◀ ▶ buttons. Facts that change fast are never
asserted on a slide as current without a source and a flag (section 6).

### 1.5 What is printed

Printable pages, print CSS only, "🖨️ Stampa" button that calls
`window.print()`; the browser's "Salva come PDF" makes the PDF:

- `/vero-o-falso/carte?copie=3` - the four answer cards, A4 portrait,
  one per page, big icon, Italian word, translations underneath.
- `/games/scheda-social` - the take-home card: A4 landscape, two A5
  copies per side, page 1 = side 1, page 2 = side 2 (print double-sided,
  short edge, cut in half).

---

## 2. The lesson, minute by minute (90 min)

| Min | Teacher | Students |
|---|---|---|
| 0-8 | Deck `lezione-8-social` slides 1-4 (pages 1-4): welcome, which apps, what they give us, today's map | log in, open "Segui la lezione"; sticky dots on the A3 sheet |
| 8-17 | 5-8: my account (8 optional) | watch, pairs check a setting |
| 17-24 | 9-11: how the feed works | "Cosa notate?" on the two feeds |
| 24-32 | 12-14: why it is hard to stop | show of hands |
| 32-41 | 15-18 (+ reveal page 19): anger and division | pairs: find the trick |
| 41-54 | 19-24 (pages 20-25): scams | silent code-word activity |
| 54-64 | 25-29 (pages 26-31): fakes and AI | vote A/B; Google Lens in pairs on their own PC |
| 64-86 | 30 (page 32): switch the projector to `/vero-o-falso` | team game with cards |
| 86-90 | 31-33 (pages 33-35): five habits, where to get help, how did it go | photo of slide 32; open the take-home card |

Parents' deck `lezione-8-genitori` (14 slides, 35-45 minutes): a separate
session or a second part; same `/present` flow, no materials.

---

## 3. Work packages, ownership and order

### 3.1 Packages

Every file has exactly one owner. Packages marked ∥ start at the same
time. Each implementer commits **only its own files**, runs
`make lint && make test`, then `git pull --rebase && git push` to `main`
(maintainer rule). Commit messages end with the session's attribution
lines.

| WP | Name | Owns (create or modify) | Needs | Start |
|---|---|---|---|---|
| A | Materials backend | `.gitignore`; `apps/web/src/rev_babel_web/materials.py`, `media_clean.py`, `materials_manifest.json`; `apps/web/tests/test_media_clean.py`, `test_materials.py` | - | ∥ first |
| B | Materials page | `apps/web/templates/materials.html`; `apps/web/static/lessons/lezione-8/materiali/materiali.js` | the API contract in 4.4 (not A's code) | ∥ |
| C1 | Decks | `apps/web/src/rev_babel_web/decks/lezione-8-social.json`, `decks/lezione-8-genitori.json`, `decks.py`; `apps/web/tests/test_lesson8_decks.py` | - | ∥ |
| C2 | Presenter and deck CSS | `apps/web/static/style.css`, `apps/web/templates/present.html`, `apps/web/templates/present_remote.html` | class names in 5.2, endpoints in 9 | ∥ |
| D | Game | `apps/web/src/rev_babel_web/vero_o_falso.json`, `vero_o_falso.py`; `apps/web/templates/games/vero_o_falso.html`, `games/vero_o_falso_carte.html`, `games/_vof_icons.html`; `apps/web/static/lessons/lezione-8/vero-o-falso/game.js`; `apps/web/tests/test_vero_o_falso.py` | status shape in 4.3 (not A's code) | ∥ |
| E | Take-home card | `apps/web/src/rev_babel_web/scheda_social.json`, `scheda_social.py`; `apps/web/templates/games/scheda_social.html`; `apps/web/tests/test_scheda_social.py` | - | ∥ |
| G | Docs | `docs/decisions/0020-lesson-8-materials-store-and-game.md`, `docs/data-and-privacy.md`, `docs/architecture.md`, `data/README.md`, `apps/web/static/README.md`, `apps/web/templates/README.md` | text in 10 | ∥ |
| F | Integration (the lead) | `apps/web/src/rev_babel_web/main.py`, `.env.example`, `apps/web/tests/test_lesson8_routes.py`, `apps/web/README.md`, `ROADMAP.md` | A, B, C1, C2, D, E pushed | after |
| T | Translations (skippable) | `scripts/translate_content.py`, `scripts/README.md`, `apps/web/tests/test_translate_content.py`; then, as data only: the two lesson 8 deck JSONs, `vero_o_falso.json`, `scheda_social.json`, `strings.json` | C1, D, E pushed (it takes over their JSON files) | after, ∥ with F |

Nobody but F touches `main.py`. Nobody but C2 touches `style.css` or
`present.html`. Nobody but T touches `strings.json`. `ROADMAP.md` is F's,
written last with what was actually verified.

### 3.2 Order of commits

1. **A, commit 1:** `.gitignore` only ("Ignore data/materials explicitly
   before lesson 8 writes there"). Must be the first commit of the build.
2. **In parallel**, one or more commits each: A (rest), B, C1, C2, D, E,
   G. Suggested messages: "Add the lesson 8 materials store (manifest,
   cleaning, storage)", "Add the lesson 8 materials page", "Add lesson 8's
   two decks with presenter notes", "Add lesson 8 deck CSS, presenter
   notes panel and phone remote", "Add the lesson 8 game Vero o falso?",
   "Add the lesson 8 take-home card", "Record ADR 0020 and update the
   privacy doc for lesson 8".
3. **F**, after A, B, C1, C2, D, E are on `main`: "Wire lesson 8: routes,
   materials API, game, card (v0.21)" with `test_lesson8_routes.py`; then
   "Document lesson 8 in the README and roadmap (v0.21)".
4. **T**, after C1, D, E are on `main` (in parallel with F): "Add
   translate_content.py" then, if the key exists, "Translate lesson 8
   content (Google, unreviewed)". If F has already pushed the roadmap, T
   adds one line to F's revision entry via F (ask the lead), not by
   editing `ROADMAP.md` itself.

Nobody restarts the running service, touches Cloudflare, or reads or
prints `.env`. Deploying (restart) is the maintainer's call.

---

## 4. The materials store (WP-A backend, WP-B page)

### 4.1 Layout on disk

```
data/materials/                 # gitignored (data/* and an explicit line)
  .tmp/<uuid4 hex>              # uploads in progress; removed after use or when older than 1 hour
  S11-A/file.png                # exactly one file per slot, cleaned
  S11-A/meta.json
```

`meta.json` (written atomically: write `meta.json.tmp`, then `os.replace`):

```json
{
 "file": {"family": "image", "mime": "image/png", "ext": ".png", "size": 482113,
          "version": "a1b2c3d4e5f6", "uploaded": "2026-11-16T18:02:11", "removed": ["tEXt", "eXIf"]},
 "fields": {"caption": "Mercato del sabato mattina 🍅"},
 "skipped": false,
 "updated": "2026-11-16T18:02:11"
}
```

`version` = first 12 hex characters of the SHA-256 of the cleaned file
(cache-busting `?v=`). `removed` lists what the cleaner dropped (shown on
the page as "🧹 Tolti i dati nascosti (posizione, data...)"). No original
file name, no uploader information.

`.gitignore` gains, under "Personal data - never commit":

```
# Lesson 8 teacher-provided materials (photos, screenshots, voice) - ADR 0020
data/materials/
```

### 4.2 The manifest (`materials_manifest.json`, verbatim)

Kinds: `image` (a photo: re-encoded as JPEG), `screenshot` (an image:
kept PNG if it is PNG), `video`, `audio`. `needed`: `required` (without
it the slide shows a placeholder or the game item is skipped), `fallback`
(without it a drawn example is used), `optional` (nice to have).
`fields[].placeholder` is the default used when the teacher leaves the
field empty; for game slots it must equal the game item's Italian
caption (tested). The `answer` of a game slot must equal the game item's
`answer` (tested).

```json
{
 "version": 1,
 "artifacts": [
  {"id": "deck-main", "title": "Lezione: Social media", "deck": "lezione-8-social"},
  {"id": "deck-parents", "title": "Genitori e social media", "deck": "lezione-8-genitori"},
  {"id": "game", "title": "Gioco: Vero o falso?", "deck": null}
 ],
 "slots": [
  {
   "id": "S11-A", "artifact": "deck-main", "where": "Slide 11 · Il mio feed e il tuo",
   "title": "La pagina iniziale di YouTube: il tuo account",
   "kind": "screenshot", "needed": "required", "noFaces": false, "answer": null,
   "alt": "Pagina iniziale di YouTube, account A",
   "instructions": [
    "Apri YouTube sul computer, con il tuo account.",
    "Fai uno screenshot della pagina iniziale (Win + Maiusc + S) e incollalo qui con Ctrl + V.",
    "Va bene anche dal telefono: screenshot dell'app YouTube o Instagram."
   ],
   "safety": [
    "Taglia la parte in alto: niente nome, foto del profilo, notifiche.",
    "Evita anteprime con bambini."
   ],
   "fields": []
  },
  {
   "id": "S11-B", "artifact": "deck-main", "where": "Slide 11 · Il mio feed e il tuo",
   "title": "La pagina iniziale di YouTube: un altro account",
   "kind": "screenshot", "needed": "required", "noFaces": false, "answer": null,
   "alt": "Pagina iniziale di YouTube, account B",
   "instructions": [
    "Apri YouTube in una finestra in incognito (Ctrl + Maiusc + N), senza account: vedrai un feed diverso.",
    "Oppure l'account di un familiare, solo se è d'accordo.",
    "Stessa app e stessa grandezza della schermata A."
   ],
   "safety": [
    "Niente nomi, foto del profilo o notifiche.",
    "Evita anteprime con bambini."
   ],
   "fields": []
  },
  {
   "id": "S21", "artifact": "deck-main", "where": "Slide 21 · «Ciao mamma, ho cambiato numero»",
   "title": "Uno screenshot vero della truffa «Ciao mamma»",
   "kind": "screenshot", "needed": "fallback", "noFaces": true, "answer": null,
   "alt": "Screenshot di un messaggio truffa «Ciao mamma, ho cambiato numero»",
   "instructions": [
    "Dal tuo telefono, da un amico che è d'accordo, o da un avviso pubblico della Polizia Postale o del CERT-AgID.",
    "Se non ce l'hai, la slide mostra un esempio disegnato."
   ],
   "safety": [
    "Copri il numero di telefono e la foto del profilo (app Foto ➜ Modifica ➜ pennarello).",
    "Niente nomi veri."
   ],
   "fields": []
  },
  {
   "id": "S25-A", "artifact": "deck-main", "where": "Slide 25 · Quale foto è vera? (foto A)",
   "title": "Una foto vera, fatta da te",
   "kind": "image", "needed": "required", "noFaces": true, "answer": null,
   "alt": "Foto A",
   "instructions": [
    "Una scena di tutti i giorni: un piatto, una strada, un mercato, un parco.",
    "Meglio se un po' strana o imperfetta: così la sorpresa funziona.",
    "Diversa dalle foto del gioco (I1, I3), per non rovinare il gioco."
   ],
   "safety": [
    "Nessun volto, nessuna targa, nessun indirizzo o insegna vicino a casa tua."
   ],
   "fields": []
  },
  {
   "id": "S25-B", "artifact": "deck-main", "where": "Slide 25 · Quale foto è vera? (foto B)",
   "title": "Un'immagine creata con l'IA, simile alla foto A",
   "kind": "image", "needed": "required", "noFaces": true, "answer": null,
   "alt": "Foto B",
   "instructions": [
    "Con Gemini o ChatGPT: «Crea una foto realistica, fatta con il telefono, di …» (la stessa scena della foto A).",
    "Scegli il risultato più realistico."
   ],
   "safety": [
    "Nessuna persona vera, nessun marchio."
   ],
   "fields": []
  },
  {
   "id": "S28", "artifact": "deck-main", "where": "Slide 28 · Proviamo: da dove viene questa foto?",
   "title": "Una foto vecchia e vera, che Google Lens ritrova",
   "kind": "image", "needed": "required", "noFaces": true, "answer": null,
   "alt": "Foto da cercare con Google Lens",
   "instructions": [
    "Una foto di una notizia di qualche anno fa (neve, alluvione, grandine) che si trova facilmente online.",
    "Prova prima sul PC del corso: tasto destro sulla foto ➜ «Cerca immagine con Google». Deve trovare l'originale.",
    "Se vuoi, cambia qui sotto la didascalia falsa (come se fosse di oggi)."
   ],
   "safety": [
    "Niente volti riconoscibili, niente bambini."
   ],
   "fields": [
    {"key": "caption", "label": "Didascalia falsa (come se fosse di oggi)", "required": false, "max": 200,
     "placeholder": "Guardate cosa è successo OGGI in città! 😱 Condividete!", "type": "text"}
   ]
  },
  {
   "id": "S29", "artifact": "deck-main", "where": "Slide 29 · L'etichetta «Creato con IA» (facoltativa)",
   "title": "Uno screenshot con l'etichetta «Creato con IA»",
   "kind": "screenshot", "needed": "fallback", "noFaces": true, "answer": null,
   "alt": "Post con l'etichetta che dice che è fatto con l'IA",
   "instructions": [
    "Su Instagram, TikTok o YouTube trova un post con l'etichetta dell'IA (per esempio «Info sull'IA» o «Creato con IA»).",
    "Ritaglia: si deve vedere bene l'etichetta.",
    "Se non lo trovi, la slide mostra un esempio disegnato."
   ],
   "safety": [
    "Copri nome e foto di chi ha pubblicato."
   ],
   "fields": []
  },
  {
   "id": "I1", "artifact": "game", "where": "Gioco · Foto · I1",
   "title": "Una tua foto vera, recente",
   "kind": "image", "needed": "required", "noFaces": true, "answer": "vero",
   "alt": "Foto di una scena di tutti i giorni",
   "instructions": [
    "Mercato, cibo, una strada, un parco. Fotografala adesso o sceglila dalla galleria.",
    "Poi crea l'immagine I2: la stessa scena, fatta con l'IA.",
    "Se il soggetto non è un mercato, cambia la didascalia."
   ],
   "safety": [
    "Nessun volto, nessuna targa, niente vicino a casa tua."
   ],
   "fields": [
    {"key": "caption", "label": "Didascalia", "required": false, "max": 120,
     "placeholder": "Mercato del sabato mattina 🍅", "type": "text"}
   ]
  },
  {
   "id": "I2", "artifact": "game", "where": "Gioco · Foto · I2",
   "title": "Un'immagine fatta con l'IA, simile alla tua foto I1",
   "kind": "image", "needed": "required", "noFaces": true, "answer": "falso_ia",
   "alt": "Immagine di una scena di tutti i giorni",
   "instructions": [
    "In Gemini o ChatGPT: «Crea una foto realistica, fatta con il telefono, di un mercato all'aperto il sabato mattina» (adatta alla tua foto I1).",
    "Usa la stessa didascalia di I1: così la coppia è più difficile."
   ],
   "safety": [
    "Nessuna persona vera, nessun marchio."
   ],
   "fields": [
    {"key": "caption", "label": "Didascalia", "required": false, "max": 120,
     "placeholder": "Mercato del sabato mattina 🍅", "type": "text"}
   ]
  },
  {
   "id": "I3", "artifact": "game", "where": "Gioco · Foto · I3",
   "title": "Una tua foto vera «troppo perfetta»",
   "kind": "image", "needed": "required", "noFaces": true, "answer": "vero",
   "alt": "Foto molto bella",
   "instructions": [
    "Un tramonto, un piatto bellissimo, un cielo incredibile. Senza filtri.",
    "Serve a capire che bello non vuol dire falso."
   ],
   "safety": [
    "Nessun volto, niente vicino a casa tua."
   ],
   "fields": [
    {"key": "caption", "label": "Didascalia", "required": false, "max": 120,
     "placeholder": "Tramonto di ieri sera 🌅", "type": "text"}
   ]
  },
  {
   "id": "I4", "artifact": "game", "where": "Gioco · Foto · I4",
   "title": "Una tua foto vecchia e vera, con una didascalia falsa",
   "kind": "image", "needed": "required", "noFaces": true, "answer": "verificare",
   "alt": "Foto di una strada con neve o acqua",
   "instructions": [
    "Una tua foto di qualche anno fa che sembra una notizia: neve, pioggia forte, una strada allagata, una coda lunga.",
    "La didascalia dice «oggi»: è falsa. Puoi cambiarla qui sotto.",
    "Diversa dalla foto della slide 28."
   ],
   "safety": [
    "Nessun volto, nessuna targa, niente vicino a casa tua."
   ],
   "fields": [
    {"key": "caption", "label": "Didascalia falsa (dice «oggi»)", "required": false, "max": 120,
     "placeholder": "OGGI in città. Guardate che disastro! 😱 Condividete!", "type": "text"}
   ]
  },
  {
   "id": "V1", "artifact": "game", "where": "Gioco · Video · V1",
   "title": "Un tuo video vero, corto (5-10 secondi)",
   "kind": "video", "needed": "required", "noFaces": true, "answer": "vero",
   "alt": "Video di una strada o di un parco",
   "instructions": [
    "Una strada, un parco, la pioggia, il mare.",
    "Registra in 1080p, non in 4K: il file è più piccolo (massimo 90 MB)."
   ],
   "safety": [
    "Nessuna persona riconoscibile, nessuna targa, niente vicino a casa tua."
   ],
   "fields": [
    {"key": "caption", "label": "Didascalia", "required": false, "max": 120,
     "placeholder": "Una passeggiata oggi pomeriggio", "type": "text"}
   ]
  },
  {
   "id": "V2", "artifact": "game", "where": "Gioco · Video · V2",
   "title": "Un video corto fatto con l'IA",
   "kind": "video", "needed": "required", "noFaces": true, "answer": "falso_ia",
   "alt": "Video di una scena con animali o natura",
   "instructions": [
    "Con Gemini (Veo), Sora o simili: animali, una strada, la natura.",
    "5-10 secondi bastano."
   ],
   "safety": [
    "Niente persone vere, niente marchi."
   ],
   "fields": [
    {"key": "caption", "label": "Didascalia", "required": false, "max": 120,
     "placeholder": "Guardate che scena incredibile! 😍", "type": "text"}
   ]
  },
  {
   "id": "V3", "artifact": "game", "where": "Gioco · Video · V3",
   "title": "Un tuo video vero, con una didascalia sbagliata",
   "kind": "video", "needed": "required", "noFaces": true, "answer": "verificare",
   "alt": "Video di una strada",
   "instructions": [
    "Un tuo video di un altro giorno o di un'altra città.",
    "La didascalia lo fa sembrare di oggi: puoi cambiarla qui sotto."
   ],
   "safety": [
    "Nessuna persona riconoscibile, nessuna targa."
   ],
   "fields": [
    {"key": "caption", "label": "Didascalia falsa (dice «oggi»)", "required": false, "max": 120,
     "placeholder": "Ecco cosa succede OGGI in centro! 😱", "type": "text"}
   ]
  },
  {
   "id": "A1", "artifact": "game", "where": "Gioco · Voci · A1",
   "title": "Un tuo messaggio vocale vero",
   "kind": "audio", "needed": "required", "noFaces": true, "answer": "vero",
   "alt": "Messaggio vocale",
   "instructions": [
    "Premi 🎙️ Registra qui sotto, oppure registra con il telefono e carica il file.",
    "Di': «Ciao, sono [il tuo nome]. Ho un problema, mi richiami appena puoi?»",
    "Voce normale, circa 5 secondi."
   ],
   "safety": [
    "Solo la tua voce. Nessun'altra persona in sottofondo.",
    "Dopo la lezione cancellalo da qui (pulsante Elimina)."
   ],
   "fields": []
  },
  {
   "id": "A2", "artifact": "game", "where": "Gioco · Voci · A2",
   "title": "La stessa frase, con la tua voce copiata dall'IA",
   "kind": "audio", "needed": "required", "noFaces": true, "answer": "falso_ia",
   "alt": "Messaggio vocale",
   "instructions": [
    "Usa un servizio di copia della voce con la tua voce e il tuo consenso.",
    "Fai dire la stessa frase di A1.",
    "Subito dopo, cancella la voce copiata dal servizio."
   ],
   "safety": [
    "Solo la TUA voce. Mai la voce di una corsista, di un collega o di chiunque altro.",
    "Dopo la lezione cancellalo anche da qui."
   ],
   "fields": []
  },
  {
   "id": "M1", "artifact": "game", "where": "Gioco · Messaggi · M1",
   "title": "Screenshot vero della truffa «Ciao mamma, ho cambiato numero»",
   "kind": "screenshot", "needed": "fallback", "noFaces": true, "answer": "truffa",
   "alt": "Screenshot di un messaggio",
   "instructions": [
    "Diverso da quello della slide 21, se puoi. Se ne hai uno solo, mettilo qui e lascia vuota la slide 21.",
    "Senza screenshot, il gioco usa un esempio inventato."
   ],
   "safety": [
    "Copri numeri, nomi e foto del profilo."
   ],
   "fields": []
  },
  {
   "id": "M2", "artifact": "game", "where": "Gioco · Messaggi · M2",
   "title": "Screenshot vero di un SMS falso (pacco o pedaggio)",
   "kind": "screenshot", "needed": "fallback", "noFaces": true, "answer": "truffa",
   "alt": "Screenshot di un SMS",
   "instructions": [
    "Dal tuo telefono, da un amico, o da un avviso pubblico (Polizia Postale, CERT-AgID).",
    "Senza screenshot, il gioco usa un esempio inventato."
   ],
   "safety": [
    "Copri numeri e link: nessun link deve essere leggibile."
   ],
   "fields": []
  },
  {
   "id": "M3", "artifact": "game", "where": "Gioco · Messaggi · M3",
   "title": "Screenshot vero di «lavoro facile: metti like e guadagni»",
   "kind": "screenshot", "needed": "fallback", "noFaces": true, "answer": "truffa",
   "alt": "Screenshot di un messaggio",
   "instructions": [
    "Dal tuo telefono, da un amico, o da un avviso pubblico.",
    "Senza screenshot, il gioco usa un esempio inventato."
   ],
   "safety": [
    "Copri numeri, nomi e link."
   ],
   "fields": []
  },
  {
   "id": "M4", "artifact": "game", "where": "Gioco · Messaggi · M4",
   "title": "Screenshot di un SMS vero e onesto",
   "kind": "screenshot", "needed": "fallback", "noFaces": true, "answer": "vero",
   "alt": "Screenshot di un SMS",
   "instructions": [
    "Per esempio un avviso di consegna di un corriere vero, o un codice della banca che hai chiesto tu.",
    "Deve essere davvero un messaggio vero.",
    "Senza screenshot, il gioco usa un esempio inventato."
   ],
   "safety": [
    "Copri codici, nomi, numeri e indirizzi."
   ],
   "fields": []
  },
  {
   "id": "M5", "artifact": "game", "where": "Gioco · Messaggi · M5",
   "title": "Screenshot di un messaggio WhatsApp vero di un ente",
   "kind": "screenshot", "needed": "fallback", "noFaces": true, "answer": "vero",
   "alt": "Screenshot di un messaggio WhatsApp",
   "instructions": [
    "Per esempio dagli operatori del corso o da una scuola.",
    "Chiedi il permesso a chi l'ha mandato.",
    "Senza screenshot, il gioco usa un esempio inventato."
   ],
   "safety": [
    "Copri nomi, numeri e foto."
   ],
   "fields": []
  },
  {
   "id": "P1", "artifact": "game", "where": "Gioco · Post · P1",
   "title": "Screenshot di un titolo vero di un giornale affidabile, con il link",
   "kind": "screenshot", "needed": "required", "noFaces": true, "answer": "vero",
   "alt": "Titolo di un giornale",
   "instructions": [
    "Un giornale italiano conosciuto, una notizia tranquilla: meteo, sport, cultura, scienza.",
    "Niente politica, migrazione, religione.",
    "Incolla il link qui sotto: lo mostriamo con la risposta."
   ],
   "safety": [
    "Se c'è una foto con volti, ritaglia solo il titolo."
   ],
   "fields": [
    {"key": "link", "label": "Link della notizia", "required": true, "max": 500,
     "placeholder": "https://", "type": "url"}
   ]
  },
  {
   "id": "F1", "artifact": "game", "where": "Gioco · Profili · F1",
   "title": "Screenshot del profilo social vero dell'ente che organizza il corso",
   "kind": "screenshot", "needed": "required", "noFaces": true, "answer": "vero",
   "alt": "Screenshot di un profilo social",
   "instructions": [
    "Oppure di un altro ente vero e conosciuto (una biblioteca, un museo).",
    "Si devono vedere: il nome, il numero di post, da quanto tempo esiste."
   ],
   "safety": [
    "Copri i volti nelle foto dei post."
   ],
   "fields": []
  },
  {
   "id": "F2", "artifact": "game", "where": "Gioco · Profili · F2 (la foto del profilo falso)",
   "title": "(Facoltativo) Un volto inventato, fatto con l'IA",
   "kind": "image", "needed": "optional", "noFaces": false, "answer": "falso_ia",
   "alt": "Foto del profilo",
   "instructions": [
    "Con Gemini o ChatGPT: «Ritratto realistico di una donna inventata, stile foto del profilo».",
    "Senza, il profilo falso mostra un'icona."
   ],
   "safety": [
    "Solo un volto inventato. Mai la foto di una persona vera."
   ],
   "fields": []
  },
  {
   "id": "F3", "artifact": "game", "where": "Gioco · Profili · F3",
   "title": "Esempio vero di una pagina che finge di essere un'azienda o un ufficio",
   "kind": "screenshot", "needed": "fallback", "noFaces": true, "answer": "truffa",
   "alt": "Screenshot di una pagina falsa",
   "instructions": [
    "Da un avviso pubblico (Polizia Postale, CERT-AgID, la tua banca).",
    "Senza screenshot, il gioco usa un esempio inventato."
   ],
   "safety": [
    "Copri link, numeri e codici: niente deve essere usabile."
   ],
   "fields": []
  }
 ]
}
```

The parents' deck needs no material: its progress line reads "Niente da
fornire ✅".

### 4.3 `materials.py` (WP-A) - public API

```python
MATERIALS_DIR = Path(os.environ.get("DATA_DIR", "data")) / "materials"  # read at call time via the module global, so tests can monkeypatch it
MANIFEST_PATH = Path(__file__).parent / "materials_manifest.json"
SLOT_ID_RE = re.compile(r"^[A-Z][0-9]{1,2}(?:-[A-Z])?$")
SLOT_TAG_RE = re.compile(
    r"<rb-slot data-slot=([\"'])(?P<id>[A-Z][0-9]{1,2}(?:-[A-Z])?)\1"
    r"(?: data-field=([\"'])(?P<field>[a-z_]{1,20})\3)?>(?P<inner>.*?)</rb-slot>",
    re.DOTALL,
)
KIND_FAMILY = {"image": "image", "screenshot": "image", "video": "video", "audio": "audio"}
LIMITS = {"image": 15 * 2**20, "video": 90 * 2**20, "audio": 20 * 2**20}
MAX_UPLOAD_BYTES = max(LIMITS.values())
MAX_TOTAL_BYTES = 2 * 2**30
ADMIN_FILE_URL = "/admin/materials/{id}/file?v={v}"
STUDENT_FILE_URL = "/api/live/material/{id}?v={v}"
STATES = ("mancante", "incompleto", "pronto", "saltato")

class MaterialError(Exception):            # .status (int HTTP code), .message (Italian, shown to the teacher)

def manifest() -> dict                     # loaded once, cached
def validate_manifest(data: dict) -> list[str]   # [] when valid
def slot(slot_id: str) -> dict | None      # None unless SLOT_ID_RE matches AND the id is in the manifest
def limit_for(slot_id: str) -> int         # LIMITS[KIND_FAMILY[kind]]
def status(slot_id: str) -> dict           # shape below
def all_status() -> list[dict]             # manifest order
def summary() -> list[dict]                # per artifact, below
def page_data() -> dict                    # {"artifacts": summary(), "slots": [{**manifest_slot, "status": status}], "limits": LIMITS}
def new_tmp_path() -> Path                 # MATERIALS_DIR/.tmp/<uuid4 hex>; creates dirs; deletes .tmp files older than 1 hour
def store_upload(slot_id: str, tmp_path: Path) -> dict   # sniff, check, clean, hash, move, write meta; returns status
def delete_file(slot_id: str) -> dict
def set_fields(slot_id: str, values: dict[str, str]) -> dict
def set_skipped(slot_id: str, skipped: bool) -> dict
def delete_all() -> None                   # removes MATERIALS_DIR entirely
def file_for(slot_id: str) -> tuple[Path, str] | None   # (path, mime) of the stored file
def slots_in_html(html: str) -> set[str]
def render_slots(html: str, audience: str) -> str       # audience "admin" or "student"
```

**Status shape** (what B's page and D's game consume; the URL is always
the admin one):

```json
{
 "id": "I1",
 "state": "pronto",
 "skipped": false,
 "file": {"family": "image", "mime": "image/jpeg", "size": 312004, "version": "a1b2c3d4e5f6",
          "uploaded": "2026-11-16T18:02:11", "removed": ["APP1"],
          "url": "/admin/materials/I1/file?v=a1b2c3d4e5f6"},
 "fields": {"caption": "Mercato in piazza"},
 "updated": "2026-11-16T18:02:11"
}
```

`file` is `null` when nothing is stored. `fields` holds only non-empty
values the teacher set. **State rules:** `saltato` if skipped; else
`pronto` if the file is present (when the slot has a `kind`) and every
`required` field is non-empty; else `incompleto` if anything is present;
else `mancante`.

**Summary entry:** `{"id", "title", "total", "ready", "missing",
"incomplete", "skipped", "missingIds": [...], "nothingNeeded": bool}`
where `total` counts non-skipped slots of that artifact, `ready` counts
`pronto`, and `nothingNeeded` is true when the artifact has no slots.

**`store_upload` steps:** unknown slot → `MaterialError(404, "Materiale
sconosciuto.")`; read the first 64 bytes, `media_clean.sniff` (→ 415 with
its Italian message); the family must fit the slot (`image` slot ←
`image`; `video` slot ← `av`; `audio` slot ← `audio` or `av`; otherwise
415 "Questo spazio vuole una foto / un video / un audio."); size over
`limit_for` → 413 "File troppo grande: massimo N MB."; store total plus
this file over `MAX_TOTAL_BYTES` → 413 "Spazio finito: elimina qualche
file."; `media_clean.clean_file` (→ 415 on a damaged file); hash; delete
any previous `file.*` of that slot; `os.replace` into `<SLOT>/file<ext>`;
write meta (keeping fields and turning `skipped` off). For an `av` file
stored in an audio slot, the mime becomes `audio/mp4` or `audio/webm`.
A `threading.Lock` per slot serialises writes (one uvicorn worker).

**`set_fields`:** unknown key → 400 "Campo sconosciuto."; value stripped;
longer than the field's `max` → 400; a `url` field must match
`^https?://\S+$` (else 400 "Il link deve iniziare con https://"); empty
string removes the value. Text is stored as typed (it is escaped when
rendered).

### 4.4 HTTP API for the materials page (implemented by F, used by B)

All on the capture host only (403 elsewhere). When `MATERIALS_KEY` is
set, all of these except the file GET also need the session flag (401
`{"detail": "Serve la chiave dei materiali."}`). Errors are JSON
`{"detail": "<Italian message>"}`.

| Method and path | Body | Returns |
|---|---|---|
| `GET /materiali` (`?k=<key>` optional) | - | the page (or the key form) |
| `POST /materiali/chiave` | form `key` | 303 to `/materiali`, or the form with an error |
| `GET /admin/api/materials` | - | `page_data()` plus `"keyConfigured": bool` |
| `POST /admin/api/materials/{slot}/file` | **raw file bytes** (not multipart), any `Content-Type` | status; 404/413/415/400 |
| `DELETE /admin/api/materials/{slot}/file` | - | status |
| `POST /admin/api/materials/{slot}/fields` | `{"fields": {"caption": "..."}}` | status; 400 |
| `POST /admin/api/materials/{slot}/skip` | `{"skipped": true}` | status |
| `POST /admin/api/materials/delete-all` | `{"confirm": "ELIMINA"}` | `{"ok": true}`; 400 otherwise |
| `GET /admin/materials/{slot}/file` | - | the file (Range supported), `Cache-Control: private, max-age=86400`, `X-Content-Type-Options: nosniff` |
| `GET /api/live/material/{slot}` (student host, login) | - | the file only while the live local slide contains the slot; else 404 |

The upload body is raw so the server can stream it to `.tmp/` with a
running byte count and stop at the cap (Starlette's multipart parser does
not cap file parts and spools them to `/tmp`).

### 4.5 `media_clean.py` (WP-A, stdlib only)

```python
class Unsupported(Exception):      # .message: Italian, for the teacher

def sniff(head: bytes) -> tuple[str, str, str]   # (family, mime, ext); family in "image", "av", "audio"
def clean_file(path: Path, mime: str) -> list[str]   # cleans in place, returns what was removed; raises Unsupported if malformed
def strip_jpeg(data: bytes) -> tuple[bytes, list[str]]
def strip_png(data: bytes) -> tuple[bytes, list[str]]
def strip_webp(data: bytes) -> tuple[bytes, list[str]]
def strip_mp3(data: bytes) -> tuple[bytes, list[str]]
def strip_wav(data: bytes) -> tuple[bytes, list[str]]
def neutralise_mp4(path: Path) -> list[str]      # in place, streaming; never loads the file
```

**`sniff` table** (first match wins):

| Magic | Result |
|---|---|
| `FF D8 FF` | `("image", "image/jpeg", ".jpg")` |
| `89 50 4E 47 0D 0A 1A 0A` | `("image", "image/png", ".png")` |
| `RIFF....WEBP` | `("image", "image/webp", ".webp")` |
| `....ftyp` + brand in `heic heix heim heis hevc hevx mif1 msf1 avif` | `Unsupported("Foto HEIC o AVIF: sul telefono scegli «Più compatibile», oppure carica la foto da questa pagina con 📷.")` |
| `....ftyp` + brand `M4A ` or `M4B ` | `("av", "audio/mp4", ".m4a")` |
| `....ftyp` (any other brand, including `qt  `) | `("av", "video/mp4", ".mp4")` |
| `1A 45 DF A3` | `("av", "video/webm", ".webm")` |
| `OggS` | `("audio", "audio/ogg", ".ogg")` |
| `RIFF....WAVE` | `("audio", "audio/wav", ".wav")` |
| `ID3`, or `FF` followed by a byte with the top three bits set | `("audio", "audio/mpeg", ".mp3")` |
| anything else | `Unsupported("Tipo di file non riconosciuto. Vanno bene: foto JPG o PNG, video MP4, audio MP3, M4A, OGG o WAV.")` |

**Rules:**

- JPEG: walk segments after `FFD8`. Copy `D0`-`D7`/`01` markers as they
  are. At `DA` (start of scan) copy everything that remains and stop.
  For every other marker read the two-byte big-endian length (it counts
  itself). Drop `E1`-`EF` and `FE`, except `E2` whose payload starts
  with `ICC_PROFILE\0` and `EE` (Adobe). Keep `E0` and everything else.
  Record dropped markers as `"APP1"`, `"COM"`... A segment running past
  the end → `Unsupported("File rovinato o incompleto.")`.
- PNG: chunks are length (4, BE), type (4), data, CRC (4). Keep only
  `IHDR PLTE IDAT IEND tRNS cHRM gAMA iCCP sBIT sRGB bKGD pHYs acTL fcTL
  fdAT cICP`; drop the rest and record their types.
- WebP: RIFF chunks (FourCC, little-endian size, data padded to even).
  Drop `EXIF` and `XMP `; in a `VP8X` chunk clear flag bits `0x08`
  (EXIF) and `0x04` (XMP) of its first byte; rewrite the RIFF size.
- WAV: keep `fmt `, `data` and `fact` chunks only (respect padding);
  rewrite the RIFF size.
- MP3: remove leading ID3v2 tags (size = synchsafe bytes 6-9, plus 10,
  plus 10 more if flag `0x10`), repeatedly; remove a trailing 128-byte
  `TAG` block. Then the data must start with a frame sync, else
  `Unsupported`.
- MP4 family (`neutralise_mp4`): open `r+b`; the first box must be
  `ftyp`. Walk boxes (32-bit size; `1` means a 64-bit size follows; `0`
  means "to the end of the parent"); a size that does not fit →
  `Unsupported("File video rovinato o incompleto.")`. Descend into
  `moov`, `trak`, `mdia`, `minf`, `edts`; never into `mdat`. Any `udta`,
  `meta` or `uuid` box met at the top level or inside those containers:
  overwrite its 4-byte type with `free` and its payload with zeros
  (1 MiB chunks); do not descend into it. File size and every other
  offset stay the same, so the video still plays.
- Ogg and WebM: unchanged, `clean_file` returns `[]`.
- `clean_file` reads the whole file for images, MP3 and WAV (at most
  20 MB) and writes the result back with `os.replace` via a sibling temp
  file.

### 4.6 `render_slots(html, audience)` (WP-A)

Applies `SLOT_TAG_RE` to every `<rb-slot>`:

- **with `data-field`:** if the teacher set that field, the escaped value
  (`html.escape`, quote=True), else `inner` unchanged (the authored,
  translatable default).
- **without `data-field`**, when the slot has a file and is not skipped:
  - image: `<figure class="slot-media"><img class="slot-img" src="URL" alt="ALT"></figure>`
  - video: `<figure class="slot-media"><video class="slot-video" src="URL" controls playsinline preload="metadata"></video></figure>`
  - audio: `<figure class="slot-media"><audio class="slot-audio" src="URL" controls preload="metadata"></audio></figure>`

  `URL` from `ADMIN_FILE_URL` or `STUDENT_FILE_URL` by audience, `ALT`
  from the manifest, both escaped.
- **otherwise:** `inner` if it is not blank (the drawn fallback), else
  `<div class="slot-missing"><span class="slot-missing-emoji">📦</span>Materiale in arrivo<small>ID</small></div>`.
- An id not in the manifest renders the missing box (tests make sure
  none exist).

`slots_in_html` returns the set of ids in `SLOT_TAG_RE` matches.

### 4.7 The materials page (WP-B): `templates/materials.html` + `materiali.js`

Standalone page (does not extend `_base.html`), Italian only,
`<meta name="viewport" content="width=device-width, initial-scale=1">`,
system font 18px, everything one column up to 40rem wide, cards full
width on a phone. Template context from F: `needs_key` (bool),
`key_error` (bool), `key_configured` (bool). If `needs_key`: only a small
form ("🔑 Chiave dei materiali", password input named `key`, "Entra",
`POST /materiali/chiave`, and "Chiave sbagliata." when `key_error`).
Otherwise the page loads
`/static/lessons/lezione-8/materiali/materiali.js?v={{ static_version }}`
which fetches `GET /admin/api/materials` and draws everything.

**Wireframe (phone):**

```
┌───────────────────────────────────────────┐
│ 📦 Materiali · Lezione 8                   │
│ Lezione  ▓▓▓▓░░░  4 di 7                   │
│ Genitori niente da fornire ✅              │
│ Gioco    ▓▓▓░░░░  7 di 18                  │
│ [ Tutto ]  [ Cosa manca (14) ]             │  sticky tabs
│ (yellow, only if !keyConfigured)           │
│ ℹ️ Pagina senza chiave: chi conosce questo │
│ indirizzo può caricare file. Aggiungi      │
│ MATERIALS_KEY nel file .env.               │
├── Lezione: Social media ──────────────────┤
│ ┌───────────────────────────────────────┐ │
│ │ S11-A · Slide 11 · Il mio feed…  🔴 Mancante │
│ │ La pagina iniziale di YouTube: il tuo │ │
│ │ account                               │ │
│ │ • Apri YouTube sul computer…          │ │  instructions
│ │ ⚠️ Taglia la parte in alto…           │ │  safety (amber)
│ │ 🙅 Niente volti  (if noFaces)         │ │
│ │ ┌───────────────────────────────────┐ │ │
│ │ │ 📷  Tocca per scegliere o          │ │ │  drop zone = <label>
│ │ │     fotografare                    │ │ │  for a hidden file input
│ │ │ oppure trascina qui · Ctrl+V       │ │ │
│ │ └───────────────────────────────────┘ │ │
│ │ [📋 Incolla]  (screenshot kinds)      │ │
│ │ [🎙️ Registra] (audio kinds)           │ │
│ │ Didascalia [Mercato del sabato…   ]   │ │  fields (placeholder = default)
│ │ ☐ Salta questo materiale              │ │
│ └───────────────────────────────────────┘ │
│ ┌ I1 · Gioco · Foto · I1  🟢 Pronto  ▸ ┐  │  ready: folded, thumbnail
│ └───────────────────────────────────────┘ │
│ … Gioco: Vero o falso? …                  │
│ ──────────────────────────────────────── │
│ 🗑️ Elimina tutto il materiale (after the  │
│ course): type ELIMINA to confirm          │
│ I file restano solo su questo computer    │
│ (data/materials), mai su GitHub.          │
└───────────────────────────────────────────┘
```

**Behaviour (`materiali.js`):**

- Badges: 🔴 Mancante, 🟠 Incompleto, 🟢 Pronto, ⚪ Saltato; `fallback`
  slots that are missing show "🟡 C'è un esempio di riserva" instead of
  🔴; `optional` ones "⚪ Facoltativo". Game slots also show "Risposta nel
  gioco: ✅ VERO" (the four labels of section 7.1).
- Ready cards are folded to one line with a small thumbnail; tap to
  unfold. Missing ones are unfolded. Order: manifest order, grouped by
  artifact.
- **Choosing a file:** the drop zone is a `<label>` for
  `<input type="file" hidden>` with `accept` = `image/*` (image,
  screenshot), `video/*` (video), `audio/*,.m4a,.mp3,.ogg,.opus,.wav`
  (audio). No `capture` attribute, so a phone offers camera **and**
  gallery. Drag and drop on the zone. A card is "active" when tapped or
  focused (`tabindex="0"`, highlighted border); `paste` on the document
  sends the first image in the clipboard to the active card, or shows
  "Tocca prima una scheda, poi incolla". "📋 Incolla" uses
  `navigator.clipboard.read()` when available, else hides itself.
- **Before sending an image:** `createImageBitmap(file, {imageOrientation: "from-image"})`,
  scale so the long side is at most 2,000 px (`image`) or 2,400 px
  (`screenshot`), draw on a canvas, `toBlob` as `image/png` if the slot is
  `screenshot` and the source is PNG, else `image/jpeg` quality 0.88. If
  decoding fails, send the original (the server decides; HEIC gets its
  explanation).
- **Recording (audio slots):** "🎙️ Registra" uses
  `navigator.mediaDevices.getUserMedia({audio: true})` and `MediaRecorder`
  (whatever type the browser picks); "⏹ Stop" after at most 60 s; preview
  with an `<audio controls>`; "⬆️ Usa questa registrazione" uploads it;
  "Rifai" discards it. The stream's tracks are stopped as soon as
  recording stops. Hidden if `MediaRecorder` is missing.
- **Upload:** `XMLHttpRequest` `POST /admin/api/materials/{id}/file`, the
  Blob as body, a progress bar from `upload.onprogress`; on success
  redraw the card from the returned status; on error show `detail` in red
  in the card. Client-side size check against `limits` first (same
  message as the server).
- **Preview:** image `<img>`, video `<video controls playsinline>`, audio
  `<audio controls>`, from `status.file.url`. Under it: size, "🧹 Tolti i
  dati nascosti" if `removed` is not empty, "🔁 Sostituisci" (opens the
  chooser) and "🗑️ Elimina" (confirm: "Eliminare questo file?").
- **Fields:** inputs prefilled with the teacher's value, placeholder =
  the default; save on `change` and on blur (`POST .../fields`), show
  "✓ salvato" for 2 s, or the error. `type="url"` for url fields.
- **Skip:** checkbox → `POST .../skip`.
- **Tabs:** "Tutto" / "Cosa manca (N)" where N counts `mancante` and
  `incompleto` among `required` slots (fallback and optional ones are
  listed after a divider "Facoltativi: c'è già un esempio"). "📋 Copia la
  lista" copies plain text, one line per slot: `S11-A - Slide 11 · Il mio
  feed e il tuo - La pagina iniziale di YouTube: il tuo account`.
- **Delete all:** a button revealing an input; enabled only when it
  reads `ELIMINA`; `POST .../delete-all`.
- After every action re-fetch `GET /admin/api/materials` to refresh the
  progress lines (cheap).
- All teacher text and server messages via `textContent`; no
  `innerHTML` with data. No `localStorage`.

---

## 5. The two decks (WP-C1 content and `decks.py`, WP-C2 CSS and presenter)

### 5.1 Format

Each deck is `{"title": ..., "slides": [...]}` as today. Each slide is:

```json
{"id": "S11", "it": "<html>", "notes": "English notes", "verify": ["VERIFY ..."], "optional": true}
```

`verify` and `optional` only where given below. Translations (WP-T) add
`en`, `fr`, `ckb`, `kmr`, `ar` keys beside `it`. Language keys are
`decks.LANG_KEYS = ("it", "en", "fr", "ckb", "kmr", "ar")`; every other
key is metadata.

**How to build the JSON:** write a throwaway generator in your scratchpad
(never committed) that holds each slide's HTML below as a Python string,
expands `{{ROUTE n}}`, and writes the file with
`json.dumps(deck, ensure_ascii=False, indent=1)` plus a final newline.
Copy the HTML **verbatim**.

**`{{ROUTE n}}` (main deck only).** Labels, in order: `1 Account`,
`2 Il feed`, `3 Il tempo`, `4 La rabbia`, `5 Truffe e falsi`, `🎮 Gioco`.
Expands to `<div class="route">` + for each label i (1-6) a
`<span class="stop done">` if i < n, `<span class="stop now">` if i == n,
else `<span class="stop ">` (with the trailing space, like the lesson 5
deck), the label, `</span>` + `</div>`. `n` = 0 marks nothing,
`n` = 7 marks all done.

Common snippet for numbered markers (as in the lesson 7 deck):
`<span class="notranslate" translate="no">1</span>` is written below as
`NT(1)`; expand it literally. Brand and page names are wrapped the same
way where shown.

**Deck titles:** `lezione-8-social.json` → `"Social media: come funzionano e come usarli in sicurezza"`;
`lezione-8-genitori.json` → `"Genitori e social media: come accompagnare i figli"`.

### 5.2 Deck CSS (WP-C2)

Add after the lesson 7 block in `style.css`, each selector written twice
(prefixed `.slide-box ` and `#local-slide `, as the lesson 5 and 7 blocks
do), and once (prefixed `#local-slide `) in `present.html`'s `<style>`.
`rb-slot` is written as `.slide-box rb-slot` / `#local-slide rb-slot`.

```css
/* ---- Lesson 8 deck vocabulary: material slots, A/B pairs, social posts,
   phone numbers, an age bar. Material is rendered server-side into
   rb-slot (ADR 0020). ---- */
rb-slot { display: block; }
.slot-media { margin: 0.5rem auto; text-align: center; }
.slot-img { display: block; max-width: 100%; max-height: 13em; margin: 0 auto; border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.18); object-fit: contain; }
.slot-video { display: block; max-width: 100%; max-height: 13em; margin: 0 auto; border-radius: 10px; background: #000; }
.slot-audio { width: 100%; max-width: 22rem; }
.slot-missing { max-width: 22rem; margin: 0.5rem auto; padding: 1.1rem 1rem; border: 3px dashed #b9c2d0;
  border-radius: 14px; background: #f5f7fb; color: #556; text-align: center; font-weight: 700; }
.slot-missing-emoji { display: block; font-size: 2.2em; line-height: 1.2; }
.slot-missing small { display: block; font-weight: 400; color: #889; font-size: 0.7em; }
.pair { display: flex; gap: 1rem; align-items: flex-start; justify-content: center; margin: 0.8rem 0; }
.pair-col { flex: 1 1 0; min-width: 0; text-align: center; }
.pair .slot-img { max-height: 11em; }
.pair-tag { display: inline-flex; align-items: center; justify-content: center; width: 1.8em; height: 1.8em;
  border-radius: 50%; background: #1d2b4a; color: #fff; font-weight: 800; margin-bottom: 0.3rem; flex: 0 0 auto; }
.pic-grid.many .pic { flex: 1 1 22%; min-width: 5.5rem; }
.pic.stop { background: #fdf1f0; border-color: #f3c9c4; }
.pic.red { background: #fde8e7; border-color: #f2b8b5; }
.pic.yellow { background: #fff6d6; border-color: #f5d76e; }
.mock-post { max-width: 24rem; margin: 0.6rem auto; background: #fff; border: 1px solid #dde1e7; border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); text-align: start; overflow: hidden; font-size: 0.8em; }
.post-head { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.7rem; }
.post-avatar { flex: 0 0 auto; width: 2.2em; height: 2.2em; border-radius: 50%; background: #e8f0fe;
  display: flex; align-items: center; justify-content: center; font-size: 1.1em; overflow: hidden; }
.post-page { font-weight: 700; color: #111; }
.post-meta { display: block; font-size: 0.75em; color: #777; font-weight: 400; }
.post-body { padding: 0 0.7rem 0.5rem; line-height: 1.4; }
.post-media { background: #e9ecf1; color: #556; text-align: center; padding: 1.1rem 0.5rem; font-size: 1.6em; }
.post-bar { display: flex; gap: 1rem; flex-wrap: wrap; padding: 0.4rem 0.7rem; border-top: 1px solid #eee; color: #666; font-size: 0.8em; }
.post-comment { margin: 0.4rem 0.7rem 0.6rem; background: #f0f2f5; border-radius: 12px; padding: 0.4rem 0.7rem; }
.post-verdict { margin: 0.3rem 0.7rem 0.6rem; padding: 0.3rem 0.6rem; border-radius: 8px; background: #fdece6;
  color: #c0392b; font-weight: 700; }
.post-row { display: flex; gap: 0.6rem; align-items: stretch; }
.post-row .mock-post { flex: 1 1 0; min-width: 0; margin: 0.4rem 0; }
.ai-label { display: inline-block; margin: 0.4rem 0.7rem 0.6rem; padding: 0.15rem 0.6rem; border-radius: 999px;
  background: #eef0f3; color: #333; font-size: 0.85em; font-weight: 700; }
.num-grid { display: flex; flex-wrap: wrap; gap: 0.8rem; margin: 1rem 0; }
.num-card { flex: 1 1 40%; min-width: 9rem; box-sizing: border-box; padding: 0.7rem 0.9rem; border-radius: 14px;
  background: #f5f7fb; border: 1px solid #dfe5f1; text-align: center; }
.num-label { display: block; font-weight: 600; }
.num-big { display: block; font-size: 1.5em; font-weight: 800; color: #1a56c4; direction: ltr; unicode-bidi: isolate;
  overflow-wrap: anywhere; }
.num-card small { display: block; font-size: 0.7em; color: #555; }
.age-bar { position: relative; height: 1.2em; margin: 2em 0.6em 0.3em; border-radius: 999px; background: #e9ecf1; direction: ltr; }
.age-fill { position: absolute; left: 0; top: 0; bottom: 0; width: 77.8%; border-radius: 999px 0 0 999px; background: #f8cdbc; }
.age-mark { position: absolute; top: -1.7em; transform: translateX(-50%); font-weight: 800; color: #1d2b4a; }
.age-mark::after { content: ""; position: absolute; left: 50%; top: 1.4em; width: 3px; height: 1.7em;
  margin-left: -1.5px; background: currentColor; }
.age-mark.m14 { left: 77.8%; }
.age-mark.m15 { left: 83.3%; color: #c0472b; }
.age-ends { display: flex; justify-content: space-between; margin: 0 0.6em 0.8rem; font-size: 0.7em; color: #777; direction: ltr; }
```

Classes reused unchanged from earlier decks: `route`/`stop`, `lead`,
`note`/`strong`, `big`, `big-emoji`, `pic-grid`/`pic`/`pic-emoji`
(+`blue green purple orange`), `ticks`/`tick`/`tick-mark`, `panels`/
`panel`/`panel-n`/`panel-art`/`panel-cap`, `handoff` and its children,
`do-list`, `signal-list`/`signal`/`signal-num`, `compare-row`/
`compare-col weak|strong`, `mock-phone` and children, `verdict-badge
safe|scam`, `bubble`.

### 5.3 Main deck `lezione-8-social.json` (35 pages)

Pages in order (index → id): 1 S01 · 2 S02 · 3 S03 · 4 S04 · 5 S05 ·
6 S06 · 7 S07 · 8 S08 · 9 S09 · 10 S10 · 11 S11 · 12 S12 · 13 S13 ·
14 S14 · 15 S15 · 16 S16 · 17 S17 · 18 S18 · **19 S18b** · 20 S19 ·
21 S20 · 22 S21 · 23 S22 · 24 S23 · 25 S24 · 26 S25 · **27 S25b** ·
28 S26 · 29 S27 · 30 S28 · 31 S29 · 32 S30 · 33 S31 · 34 S32 · 35 S33.
`S18b` and `S25b` are reveal pages (the "duplicate the slide" trick of
the lesson 2 quiz deck). Optional: `S08`, `S29`.

Every flag below starts with the same words; write them in full:
`VERIFY before class (flagged 2026-11-16, from the maintainer's research brief, not re-checked): `
(abbreviated here as **V:**).

#### Part A - Opening

**S01**
```html
<div class="big-emoji">📱💬🌍</div><h1>Social media: come funzionano e come usarli in sicurezza</h1><p class="lead">Non per smettere. Per usarli bene.</p><p class="note">Lezione 8</p>
```
Notes: "Welcome. This lesson is about using social media well, not about giving them up. Ask everyone to open 'Segui la lezione' now."

**S02**
```html
<h1>Quali usate? Per fare cosa?</h1><div class="pic-grid many"><div class="pic green"><span class="pic-emoji">💬</span><span class="notranslate" translate="no">WhatsApp</span></div><div class="pic blue"><span class="pic-emoji">👥</span><span class="notranslate" translate="no">Facebook</span></div><div class="pic purple"><span class="pic-emoji">📷</span><span class="notranslate" translate="no">Instagram</span></div><div class="pic"><span class="pic-emoji">🎵</span><span class="notranslate" translate="no">TikTok</span></div><div class="pic red"><span class="pic-emoji">▶️</span><span class="notranslate" translate="no">YouTube</span></div><div class="pic blue"><span class="pic-emoji">✈️</span><span class="notranslate" translate="no">Telegram</span></div><div class="pic yellow"><span class="pic-emoji">👻</span><span class="notranslate" translate="no">Snapchat</span></div></div><p class="note strong">Un bollino su ogni app che usate.</p>
```
Notes: "Activity, 3 min: coloured sticky dots on a printed A3 sheet or the whiteboard, one per app each learner uses. Then ask 'per fare cosa?' and write the answers on the board; keep them for slide 3. WhatsApp and Telegram groups and channels count as social media today. The learners are the experts here. No logos on purpose: generic icons, the names in text."

**S03**
```html
<h1>Cosa ci danno di buono</h1><div class="pic-grid"><div class="pic blue"><span class="pic-emoji">👨‍👩‍👧</span>La famiglia lontana<small>videochiamate e messaggi</small></div><div class="pic green"><span class="pic-emoji">💼</span>Lavoro e annunci</div><div class="pic purple"><span class="pic-emoji">👥</span>Gruppi della comunità</div><div class="pic orange"><span class="pic-emoji">📰</span>Notizie nella nostra lingua</div><div class="pic yellow"><span class="pic-emoji">📚</span>Imparare<small>italiano, ricette, corsi</small></div></div>
```
Notes: "Connect each picture to something the learners said on slide 2. These tools are valuable, which is exactly why it is worth learning how they work. Start with the value, not the risks."

**S04**
```html
{{ROUTE 0}}<h1>Oggi parliamo di</h1><div class="ticks"><div class="tick"><span class="tick-mark">🔒</span><span>1. Il mio account</span></div><div class="tick"><span class="tick-mark">🎯</span><span>2. Chi sceglie cosa vediamo</span></div><div class="tick"><span class="tick-mark">⏰</span><span>3. Perché è difficile smettere</span></div><div class="tick"><span class="tick-mark">😡</span><span>4. Rabbia e divisione</span></div><div class="tick"><span class="tick-mark">🎣</span><span>5. Truffe e contenuti falsi</span></div><div class="tick"><span class="tick-mark">🎮</span><span><strong>Poi: un gioco!</strong></span></div></div>
```
Notes: "The strip at the top of every slide shows where we are."

#### Part B - My account

**S05**
```html
{{ROUTE 1}}<h1>Chi vede quello che pubblico?</h1><div class="mock-post"><div class="post-head"><span class="post-avatar">🙂</span><span class="post-page">Io<span class="post-meta">Adesso · 🌍 ▾</span></span></div><div class="post-body">Che bella giornata al parco! ☀️</div></div><div class="ticks"><div class="tick"><span class="tick-mark">🌍</span><span><strong>Pubblico</strong>: tutti.</span></div><div class="tick"><span class="tick-mark">👥</span><span><strong>Amici</strong>: solo i miei contatti.</span></div><div class="tick"><span class="tick-mark">🔒</span><span><strong>Solo io</strong>.</span></div></div>
```
Notes: "Demo on the projector, on Facebook in the browser: where to choose who sees a post and who sees the profile (the small globe under the name). WhatsApp has the same idea for the profile photo, 'ultimo accesso' and the status."

**S06**
```html
{{ROUTE 1}}<h1>Proteggi l'account</h1><div class="ticks"><div class="tick"><span class="tick-mark">🔑</span><span>Password lunga e diversa per ogni app.</span></div><div class="tick"><span class="tick-mark">📲</span><span>Attiva la <strong>verifica in due passaggi</strong>.</span></div><div class="tick"><span class="tick-mark">🚫</span><span>Il codice che arriva per SMS non si dà <strong>MAI</strong> a nessuno.</span></div></div><div class="mock-phone"><div class="mock-phone-header"><span class="mock-sender">💬 Un'amica</span></div><div class="mock-bubble">Ciao! Ti ho mandato un codice per sbaglio, me lo giri? 🙏</div></div><div class="verdict-badge scam">❌ Mai!</div>
```
Notes: "Verifica in due passaggi = password + a code on the phone. The most common WhatsApp account theft: a friend's account, already stolen, writes 'I sent you a code by mistake, can you forward it?'. If you send it, they take your account and ask your contacts for money. The Polizia Postale has warned about this many times. Optional, with phones: show where to turn on two-step verification in WhatsApp."
Verify: `["V: WhatsApp menu path for two-step verification: Impostazioni > Account > Verifica in due passaggi."]`

**S07**
```html
{{ROUTE 1}}<h1>Cosa non pubblicare</h1><div class="pic-grid"><div class="pic stop"><span class="pic-emoji">🪪</span>🚫 Documenti<small>passaporto, permesso di soggiorno, tessera sanitaria</small></div><div class="pic stop"><span class="pic-emoji">🎫</span>🚫 Carte d'imbarco e biglietti</div><div class="pic stop"><span class="pic-emoji">🏠</span>🚫 L'indirizzo di casa</div><div class="pic stop"><span class="pic-emoji">📍</span>🚫 Dove sono adesso</div><div class="pic stop"><span class="pic-emoji">🏫</span>🚫 Foto dei bambini con il nome della scuola</div></div>
```
Notes: "Documents and boarding passes carry codes that can be used for identity fraud. 'Dove sono adesso' means live location, and holiday photos posted while the house is empty. The children point links to the parents' session."

**S08** (`"optional": true`)
```html
{{ROUTE 1}}<div class="handoff"><div class="handoff-emoji">🤝</div><div class="handoff-title">Proviamo insieme</div><span class="handoff-where">WhatsApp ➜ Impostazioni ➜ Privacy ➜ Immagine del profilo</span><span class="handoff-time">3 minuti, in coppia</span><div class="do-list"><div class="tick"><span class="tick-mark">👀</span><span>Chi vede la mia foto?</span></div><div class="tick"><span class="tick-mark">👥</span><span>Scegli: Tutti, I miei contatti, Nessuno.</span></div><div class="tick"><span class="tick-mark">💻</span><span>Senza telefono? Guardate lo schermo grande.</span></div></div></div>
```
Notes: "OPTIONAL. Pairs, on a phone if anyone wants, or the teacher on the projector. Nobody has to show her own phone."
Verify: `["V: WhatsApp menu path and option names for who sees the profile photo."]`

#### Part C - How the feed works

**S09**
```html
{{ROUTE 2}}<div class="big-emoji">🤖📱</div><h1>Chi sceglie cosa vediamo?</h1><p class="lead">Un programma: <strong>l'algoritmo</strong>. Guarda:</p><div class="ticks"><div class="tick"><span class="tick-mark">⏱️</span><span>cosa guardiamo più a lungo,</span></div><div class="tick"><span class="tick-mark">💬</span><span>cosa commentiamo,</span></div><div class="tick"><span class="tick-mark">↗️</span><span>cosa condividiamo.</span></div></div><p class="note">Algoritmo = una lista di istruzioni per il computer.</p>
```
Notes: "'Algoritmo' is a set of instructions a computer follows; here it decides which posts we see and in which order. It learns from what we do, often from things we do not notice, like slowing down on a video."

**S10**
```html
{{ROUTE 2}}<h1>È gratis. Come guadagnano?</h1><div class="panels"><div class="panel"><span class="panel-n">NT(1)</span><div class="panel-art">📱</div><div class="panel-cap">Scorriamo</div></div><div class="panel"><span class="panel-n">NT(2)</span><div class="panel-art">📢</div><div class="panel-cap">Vediamo pubblicità</div></div><div class="panel"><span class="panel-n">NT(3)</span><div class="panel-art">💶</div><div class="panel-cap">Soldi all'azienda</div></div><div class="panel"><span class="panel-n">NT(4)</span><div class="panel-art">🔁</div><div class="panel-cap">L'app ci tiene dentro</div></div></div><p class="note strong">Più tempo restiamo, più pubblicità vediamo.</p>
```
Notes: "The key idea for the rest of the lesson: the app is designed to keep our attention, because attention is what it sells to advertisers."

**S11**
```html
{{ROUTE 2}}<h1>Il mio feed e il tuo</h1><div class="pair"><div class="pair-col"><span class="pair-tag">NT(A)</span><rb-slot data-slot="S11-A"></rb-slot></div><div class="pair-col"><span class="pair-tag">NT(B)</span><rb-slot data-slot="S11-B"></rb-slot></div></div><p class="note strong">Due persone, due feed diversi. Cosa notate?</p>
```
Notes: "Activity, 2 min: 'Cosa notate?' Learners point out differences. A is the teacher's own account, B another account or no account at all. If the screenshots are missing, describe the idea and skip the slide."

#### Part D - Why it is hard to stop

**S12**
```html
{{ROUTE 3}}<div class="big-emoji">🛋️⏰</div><h1>Vi è mai successo?</h1><p class="big">«Volevo guardare 5 minuti… ed è passata un'ora.»</p><p class="note strong">🙋 Succede a tutti noi.</p>
```
Notes: "Show of hands. The teacher raises his hand first. Normalise it: this is not a personal weakness, it is the result of design choices made by large teams."

**S13**
```html
{{ROUTE 3}}<h1>Come è fatta l'app</h1><div class="pic-grid"><div class="pic blue"><span class="pic-emoji">♾️</span>Scorrimento infinito<small>non c'è una fine</small></div><div class="pic green"><span class="pic-emoji">▶️</span>Video che partono da soli</div><div class="pic purple"><span class="pic-emoji">🔔</span>Notifiche<small>ci richiamano dentro</small></div><div class="pic orange"><span class="pic-emoji">🎰</span>Sorprese<small>il prossimo video sarà bello? Continuiamo.</small></div></div><p class="note strong">Non è una nostra debolezza: l'app è fatta così.</p>
```
Notes: "The slot machine explains unpredictable rewards without technical words. Do not say 'dopamina'. Regulators take this seriously: in February 2026 the European Commission said, as a preliminary finding, that TikTok breaks the EU's Digital Services Act because of addictive design (infinite scroll, autoplay, push notifications, a very personalised recommendation system)."
Verify: `["V: outcome and current status of the European Commission's TikTok addictive-design case under the DSA (preliminary finding, February 2026)."]`

**S14**
```html
{{ROUTE 3}}<h1>Cosa possiamo fare</h1><div class="ticks"><div class="tick"><span class="tick-mark">🔕</span><span>Spegnere le notifiche che non servono.</span></div><div class="tick"><span class="tick-mark">⏳</span><span>Mettere un limite di tempo nell'app.</span></div><div class="tick"><span class="tick-mark">🙅</span><span>Toccare «Non mi interessa».</span></div><div class="tick"><span class="tick-mark">💻</span><span>Usare il computer invece del telefono.</span></div><div class="tick"><span class="tick-mark">🛏️</span><span>Di notte, telefono fuori dalla camera.</span></div></div><p class="note">Sono idee, non regole. Voi cosa fate già?</p>
```
Notes: "Options, not rules: adults decide. Ask what they already do; learners often have good strategies. Optional, with phones: everyone turns off one notification she does not need."

#### Part E - Anger and division

**S15**
```html
{{ROUTE 4}}<h1>Perché vediamo tanti post che fanno arrabbiare?</h1><div class="panels"><div class="panel"><span class="panel-n">NT(1)</span><div class="panel-art">😡</div><div class="panel-cap">Un post ci fa arrabbiare</div></div><div class="panel"><span class="panel-n">NT(2)</span><div class="panel-art sm">💬💬💬</div><div class="panel-cap">Tanti commenti</div></div><div class="panel"><span class="panel-n">NT(3)</span><div class="panel-art sm">📱📱📱</div><div class="panel-cap">Il programma lo mostra a più persone</div></div></div><p class="note strong">Rabbia = tanti commenti = più persone lo vedono.</p>
```
Notes: "A 2026 study in PNAS (a major US science journal) followed 715 users on X and found that the feed tended to amplify content that went against users' own stated values; replies were only 6.8% of interactions but seemed to weigh a lot in what the algorithm showed next. An older MIT study (2018) found that false news spread farther and faster than true news on Twitter."
Verify: `["V: the 2026 PNAS study on X's algorithm (715 users, 6.8% replies) and how it is reported."]`

**S16**
```html
{{ROUTE 4}}<h1>Anche il commento «È falso!» aiuta il post</h1><div class="mock-post"><div class="post-head"><span class="post-avatar">📣</span><span class="post-page">Una pagina qualsiasi<span class="post-meta">1 ora fa · 🌍</span></span></div><div class="post-body">Una notizia che fa arrabbiare…</div><div class="post-comment">😡 Vergogna! È falso!</div><div class="post-bar"><span>⬆️ Il post sale</span><span>💬 NT(1.240)</span></div></div><div class="ticks"><div class="tick"><span class="tick-mark">🤐</span><span>Non rispondere.</span></div><div class="tick"><span class="tick-mark">🙈</span><span>Nascondere.</span></div><div class="tick"><span class="tick-mark">🚩</span><span>Segnalare.</span></div><div class="tick"><span class="tick-mark">🗣️</span><span>Parlarne di persona.</span></div></div>
```
Notes: "Every comment, even an angry one, tells the program 'this post is interesting'. Researchers have shown that outrage-provoking false information spreads further partly because algorithms boost engaging content, even when people engage to say it is false."

**S17**
```html
{{ROUTE 4}}<h1>I trucchi più comuni</h1><div class="pic-grid"><div class="pic orange"><span class="pic-emoji">📢</span>Parole forti<small>SCANDALO! VERGOGNA! INCREDIBILE!</small></div><div class="pic purple"><span class="pic-emoji">⚔️</span>Noi contro loro</div><div class="pic blue"><span class="pic-emoji">🎭</span>Profili falsi<small>sembrano persone vere o esperti</small></div><div class="pic green"><span class="pic-emoji">📼</span>Video vecchi<small>o di un altro paese, con una storia nuova</small></div></div><p class="note strong">Chi guadagna dalla nostra rabbia?</p>
```
Notes: "A short version of the techniques taught by the Cambridge game 'Bad News'. Stay neutral on politics: teach the technique, not which side is right. If anti-migrant content comes up, acknowledge it gently without asking anyone to share."

**S18**
```html
{{ROUTE 4}}<h1>Trova il trucco</h1><div class="post-row"><div class="mock-post"><div class="post-head"><span class="pair-tag">NT(1)</span><span class="post-page"><span class="notranslate" translate="no">Notizie Che Fanno Rabbia</span><span class="post-meta">2 ore fa · 🌍</span></span></div><div class="post-body">SCANDALO!!! Il caffè al bar costa 3 EURO!!! VERGOGNA!!! 😡😡</div></div><div class="mock-post"><div class="post-head"><span class="pair-tag">NT(2)</span><span class="post-page"><span class="notranslate" translate="no">Meteo Tutto Subito</span><span class="post-meta">20 minuti fa · 🌍</span></span></div><div class="post-body">Grandine OGGI in città! Guardate! 😱</div><div class="post-media">▶️ ⛈️</div></div><div class="mock-post"><div class="post-head"><span class="pair-tag">NT(3)</span><span class="post-page"><span class="notranslate" translate="no">Tifosi Rossi Veri</span><span class="post-meta">5 ore fa · 🌍</span></span></div><div class="post-body">Noi, i tifosi veri, contro LORO: quelli della squadra Blu. O stai con noi o stai con loro!</div></div></div><p class="note strong">Quale trucco usa? In coppia, 3 minuti.</p><p class="note">Esempi creati per il corso.</p>
```
Notes: "Activity, 3 min: in pairs, match each post to a card of slide 17. Then show the next page. All three are invented: neutral topics, invented page names, invented teams."

**S18b**
```html
{{ROUTE 4}}<h1>Trova il trucco: le risposte</h1><div class="post-row"><div class="mock-post"><div class="post-head"><span class="pair-tag">NT(1)</span><span class="post-page"><span class="notranslate" translate="no">Notizie Che Fanno Rabbia</span><span class="post-meta">2 ore fa · 🌍</span></span></div><div class="post-body">SCANDALO!!! Il caffè al bar costa 3 EURO!!! VERGOGNA!!! 😡😡</div><div class="post-verdict">📢 Parole forti</div></div><div class="mock-post"><div class="post-head"><span class="pair-tag">NT(2)</span><span class="post-page"><span class="notranslate" translate="no">Meteo Tutto Subito</span><span class="post-meta">20 minuti fa · 🌍</span></span></div><div class="post-body">Grandine OGGI in città! Guardate! 😱</div><div class="post-media">▶️ ⛈️</div><div class="post-verdict">📼 Video vecchio: un altro anno, un altro paese</div></div><div class="mock-post"><div class="post-head"><span class="pair-tag">NT(3)</span><span class="post-page"><span class="notranslate" translate="no">Tifosi Rossi Veri</span><span class="post-meta">5 ore fa · 🌍</span></span></div><div class="post-body">Noi, i tifosi veri, contro LORO: quelli della squadra Blu. O stai con noi o stai con loro!</div><div class="post-verdict">⚔️ Noi contro loro</div></div></div><p class="note">Esempi creati per il corso.</p>
```
Notes: "Ask 'Come l'avete capito?'. Post 2 cannot be judged by looking: the trick is in where the video comes from, which is the bridge to part G."

#### Part F - Scams

**S19**
```html
{{ROUTE 5}}<div class="big-emoji">💶</div><h1>Le truffe online sono tante</h1><p class="big">NT(27.000+)</p><p class="lead">casi di truffe online sui soldi in Italia nel 2025 (Polizia Postale).</p><p class="note strong">Succede a tante persone. Parlarne aiuta.</p>
```
Notes: "The Polizia Postale annual report 2025 counts 27,085 cases of economic and financial cybercrime and more than 269 million euro stolen over two years. In the US, social media is the scam channel that costs victims the most (at least 2.1 billion dollars in 2025, according to the FTC, the US consumer agency); online shopping scams are the most reported kind."
Verify: `["V: Polizia Postale 2025 figures (27,085 cases; 269 million euro over two years). A 2026 report may be out: use the latest and change the slide.", "V: FTC 2025 figure for social-media scam losses."]`

**S20**
```html
{{ROUTE 5}}<h1>Tre segnali di truffa</h1><div class="signal-list"><div class="signal"><span class="signal-num">NT(1)</span><div><strong>⏱️ Fretta</strong>«Subito!»</div></div><div class="signal"><span class="signal-num">NT(2)</span><div><strong>💓 Un'emozione forte</strong>paura, amore, guadagno facile</div></div><div class="signal"><span class="signal-num">NT(3)</span><div><strong>🔒 Un pagamento strano o segreto</strong>ricarica, criptovalute, bonifico istantaneo, «non dirlo a nessuno»</div></div></div><p class="note strong">Fretta + soldi = mi fermo e controllo.</p>
```
Notes: "Almost every scam uses at least two of these. The rule: when you feel rushed and money is involved, stop and check through another channel (call the person, the bank, the office)."

**S21**
```html
{{ROUTE 5}}<h1>«Ciao mamma, ho cambiato numero»</h1><div class="pair"><div class="pair-col"><rb-slot data-slot="S21"><div class="mock-phone"><div class="mock-phone-header"><span class="mock-sender">💬 Numero sconosciuto</span></div><div class="mock-bubble">Ciao mamma, ho cambiato numero. Salva questo. Ho un problema, mi aiuti? 🙏</div></div><p class="note">Esempio creato per il corso</p></rb-slot></div><div class="pair-col"><p class="lead">Cosa fare:</p><div class="ticks"><div class="tick"><span class="tick-mark">📞</span><span>Chiamare la persona al numero vecchio.</span></div><div class="tick"><span class="tick-mark">🤐</span><span>Non rispondere.</span></div><div class="tick"><span class="tick-mark">🚫</span><span>Bloccare e segnalare.</span></div></div></div></div>
```
Notes: "This scam arrives from an unknown number, opens with 'Ciao mamma' or 'ciao papà' and 'ho cambiato numero', and soon a problem appears: broken phone, blocked account, urgent expense. Polizia Postale advice: verify by calling the person on another channel; block and report the number. The picture is the teacher's real (redacted) screenshot when provided, otherwise a drawn example."

**S22**
```html
{{ROUTE 5}}<h1>Anche la voce può essere falsa</h1><div class="pic-grid"><div class="pic purple"><span class="pic-emoji">🎙️➜🤖</span>Bastano pochi secondi di voce per copiarla.</div><div class="pic green"><span class="pic-emoji">🔑</span>Una parola segreta di famiglia ci protegge.</div></div><p class="note strong">🤫 Pensate a una parola segreta per la vostra famiglia. Non ditela ad alta voce!</p>
```
Notes: "AI tools can copy a voice from a few seconds of audio taken from social media, voicemail greetings or public videos. The simplest defence is a family code word: if someone calls in an emergency, ask for it. Silent activity, 1 min. In the game the class will hear the teacher's own voice copied by AI (made with his consent)."

**S23**
```html
{{ROUTE 5}}<h1>Altre truffe frequenti</h1><div class="pic-grid"><div class="pic orange"><span class="pic-emoji">🛒</span>Negozio online con prezzi bassissimi</div><div class="pic purple"><span class="pic-emoji">⭐</span>Una persona famosa consiglia un investimento<small>spesso è un video falso</small></div><div class="pic blue"><span class="pic-emoji">👍</span>Lavoro facile da casa<small>«metti like e guadagni»</small></div><div class="pic red"><span class="pic-emoji">💔</span>Amore online che, dopo un po', chiede soldi</div><div class="pic yellow"><span class="pic-emoji">🔁</span>«Ti aiutiamo a recuperare i soldi persi», a pagamento</div><div class="pic green"><span class="pic-emoji">📄</span>Aiuto a pagamento per documenti o permesso, da sconosciuti</div></div>
```
Notes: "Celebrity investment videos are often deepfakes (AI video of a real person). 'Task' job scams start with unsolicited messages on WhatsApp, Telegram or social media. Recovery scams target people who already lost money. For the last tile: official procedures go through the Questura, the Prefettura, patronati and organisations like the one running this course; nobody legitimate sells 'fast-track' help in a WhatsApp group. Say it calmly, without implying anyone has done it."
Verify: `["V: the FTC statistic that nearly 60% of reported romance-scam losses start on social media."]`

**S24**
```html
{{ROUTE 5}}<h1>Se è successo</h1><p class="lead">Succede a tutti: non è una colpa.</p><div class="ticks"><div class="tick"><span class="tick-mark">🏦</span><span>Chiamare subito la banca.</span></div><div class="tick"><span class="tick-mark">📸</span><span>Fare screenshot di tutto.</span></div><div class="tick"><span class="tick-mark">🛡️</span><span>Segnalare su <span class="notranslate" translate="no">commissariatodips.it</span>.</span></div><div class="tick"><span class="tick-mark">👥</span><span>Avvisare i contatti.</span></div></div>
```
Notes: "Speed and no shame. Shame is what keeps victims quiet, and that helps scammers."
Verify: `["V: the Polizia Postale reporting portal is still commissariatodips.it."]`

#### Part G - Fakes and AI

**S25**
```html
{{ROUTE 5}}<h1>Quale foto è vera?</h1><div class="pair"><div class="pair-col"><span class="pair-tag">NT(A)</span><rb-slot data-slot="S25-A"></rb-slot></div><div class="pair-col"><span class="pair-tag">NT(B)</span><rb-slot data-slot="S25-B"></rb-slot></div></div><p class="note strong">A o B? Alzate la mano.</p>
```
Notes: "Activity, 2 min: vote by raising hands, then show the next page. A is the teacher's real photo, B is made with AI. It works best when B is very realistic and A looks a bit odd."

**S25b**
```html
{{ROUTE 5}}<h1>Quale foto è vera? La risposta</h1><div class="pair"><div class="pair-col"><span class="pair-tag">NT(A)</span><rb-slot data-slot="S25-A"></rb-slot><div class="verdict-badge safe">✅ Vera</div></div><div class="pair-col"><span class="pair-tag">NT(B)</span><rb-slot data-slot="S25-B"></rb-slot><div class="verdict-badge scam">🤖 Creata con l'IA</div></div></div><p class="note strong">Guardare bene non basta più.</p>
```
Notes: "Do not dwell on 'how could you tell': the point is that often you cannot."

**S26**
```html
{{ROUTE 5}}<h1>Gli occhi non bastano più</h1><div class="compare-row"><div class="compare-col weak"><h2>🔍 Prima</h2>Guardare le mani, le scritte, le ombre.</div><div class="compare-col strong"><h2>📍 Oggi</h2>L'IA sbaglia sempre meno. La domanda giusta: <strong>da dove viene?</strong></div></div>
```
Notes: "Even experts say there is no reliable way to spot every AI fake, and no detection tool catches everything. Visual clues are sometimes useful, never a test. Checking the source is more reliable."

**S27**
```html
{{ROUTE 5}}<h1>Quattro domande prima di condividere</h1><div class="signal-list"><div class="signal"><span class="signal-num">NT(1)</span><div><strong>✋ Fermati.</strong></div></div><div class="signal"><span class="signal-num">NT(2)</span><div><strong>👤 Chi l'ha pubblicato?</strong></div></div><div class="signal"><span class="signal-num">NT(3)</span><div><strong>📰 Cosa dicono altre fonti?</strong></div></div><div class="signal"><span class="signal-num">NT(4)</span><div><strong>🔍 Dov'è l'originale?</strong></div></div></div>
```
Notes: "This is the SIFT method (Stop, Investigate the source, Find better coverage, Trace to the original) in simple Italian. Leave it visible during the hands-on. It is side 1 of the take-home card."

**S28**
```html
{{ROUTE 5}}<h1>Proviamo: da dove viene questa foto?</h1><div class="pair"><div class="pair-col"><div class="mock-post"><div class="post-head"><span class="post-avatar">📰</span><span class="post-page"><span class="notranslate" translate="no">Notizie Veloci 24</span><span class="post-meta">Oggi · 🌍</span></span></div><div class="post-body"><rb-slot data-slot="S28" data-field="caption">Guardate cosa è successo OGGI in città! 😱 Condividete!</rb-slot></div><rb-slot data-slot="S28"></rb-slot></div></div><div class="pair-col"><div class="handoff"><div class="handoff-emoji">🔍</div><div class="handoff-title"><span class="notranslate" translate="no">Google Lens</span></div><div class="do-list"><div class="tick"><span class="tick-mark">🖱️</span><span>Tasto destro sulla foto.</span></div><div class="tick"><span class="tick-mark">🔎</span><span>«Cerca immagine con Google».</span></div><div class="tick"><span class="tick-mark">📅</span><span>Da dove viene? Di quando è?</span></div></div><span class="handoff-time">4 minuti, in coppia</span></div></div></div>
```
Notes: "The teacher demonstrates on the projector first: right-click the image in Chrome, 'Cerca immagine con Google' (Google Lens). Then pairs try on their own screen, on this same image on the follow page, and find where and when it really came from. The teacher must test this image on a classroom PC before the lesson."
Verify: `["V: Chrome's right-click label for Google Lens ('Cerca immagine con Google') on the classroom PCs."]`

**S29** (`"optional": true`)
```html
{{ROUTE 5}}<h1>L'etichetta «Creato con IA»</h1><rb-slot data-slot="S29"><div class="mock-post"><div class="post-head"><span class="post-avatar">🏔️</span><span class="post-page"><span class="notranslate" translate="no">Paesaggi Belli</span><span class="post-meta">3 ore fa · 🌍</span></span></div><div class="post-media">🏔️🌅</div><div class="ai-label">🤖 Creato con IA</div></div><p class="note">Esempio creato per il corso</p></rb-slot><p class="lead">Alcune app mettono un'etichetta.</p><p class="note strong">Non sempre: spesso manca.</p>
```
Notes: "OPTIONAL. Platforms label some AI content, and some generators add invisible watermarks (Google's SynthID, C2PA content credentials). Useful when present; a missing label proves nothing."
Verify: `["V: the current wording of AI labels on Instagram, TikTok and YouTube."]`

#### Part H - Game

**S30**
```html
{{ROUTE 6}}<div class="handoff"><div class="handoff-emoji">🎮</div><div class="handoff-title">Gioco a squadre: Vero o falso?</div><span class="handoff-where">Guardate lo schermo grande</span><div class="pic-grid"><div class="pic green"><span class="pic-emoji">✅</span>VERO</div><div class="pic red"><span class="pic-emoji">🤖</span>FALSO / IA</div><div class="pic yellow"><span class="pic-emoji">🎣</span>TRUFFA</div><div class="pic blue"><span class="pic-emoji">🔍</span>DEVO VERIFICARE</div></div></div>
```
Notes: "Switch the projector to the game tab (/vero-o-falso). About 22 minutes. Hand out the four cards to each team. 'Devo verificare' is never wrong: it earns a point on hard items."

#### Part I - Closing

**S31**
```html
{{ROUTE 7}}<h1>Cinque abitudini da portare a casa</h1><div class="ticks"><div class="tick"><span class="tick-mark">📲</span><span>1. Verifica in due passaggi attiva.</span></div><div class="tick"><span class="tick-mark">🔕</span><span>2. Notifiche inutili spente.</span></div><div class="tick"><span class="tick-mark">🤐</span><span>3. Alla rabbia non rispondo.</span></div><div class="tick"><span class="tick-mark">⏱️</span><span>4. Fretta + soldi = mi fermo e chiamo.</span></div><div class="tick"><span class="tick-mark">🔍</span><span>5. Prima di condividere: da dove viene?</span></div></div>
```
Notes: "The same five habits close the game. Point to the take-home card on the lesson 8 page."

**S32**
```html
{{ROUTE 7}}<h1>Dove chiedere aiuto</h1><div class="num-grid"><div class="num-card"><span class="num-label">🛡️ Polizia Postale</span><span class="num-big notranslate" translate="no">commissariatodips.it</span></div><div class="num-card"><span class="num-label">🚨 Emergenza</span><span class="num-big notranslate" translate="no">112</span></div><div class="num-card"><span class="num-label">🏦 La propria banca</span><span class="num-big">📞</span><small>il numero è sul retro della carta</small></div><div class="num-card"><span class="num-label">🙋 Gli operatori del corso</span><span class="num-big">💬</span></div></div><p class="note strong">📸 Fate una foto a questa slide.</p>
```
Notes: "Suggest a photo of this slide. The bank's fraud number is usually printed on the back of the card."
Verify: `["V: commissariatodips.it is still the Polizia Postale portal."]`

**S33**
```html
{{ROUTE 7}}<div class="big-emoji">😀 😐 🙁</div><h1>Com'è andata?</h1><p class="lead">Cosa vi è stato più utile?</p><p class="note">Un bollino sulla lavagna.</p>
```
Notes: "Three faces on the board; each learner places a sticky dot. Then one open question."

### 5.4 Parents' deck `lezione-8-genitori.json` (14 slides, ids G01-G14)

No route strip, no material. Framing for the teacher (also in G01's
notes): involvement and supportive engagement work better than pure
control; in migrant families children are often the family's translators
and tech helpers, so reassure parents that what they know about life and
danger is what children need; be honest that the science is debated; no
panic; concrete risks such as sextortion get clear action plans; no
photos of real children.

**G01**
```html
<div class="big-emoji">👩‍👦📱</div><h1>Genitori e social media: come accompagnare i figli</h1><p class="lead">Non da soli: insieme.</p>
```
Notes: "35-45 minutes. Parents do not need to be more technical than their children. Research points to involvement and 'supportive engagement' over pure control (studies summarised in JAMA Network Open in 2026)."

**G02**
```html
<h1>Non serve essere esperti di tecnologia</h1><div class="pic-grid"><div class="pic blue"><span class="pic-emoji">📱</span>I figli conoscono le app.</div><div class="pic green"><span class="pic-emoji">🧭</span>Voi conoscete la vita, le persone, i pericoli.</div></div><p class="note strong">Servono entrambe le cose.</p>
```
Notes: "Open with a question: 'I vostri figli vi aiutano con il telefono?' Acknowledge the role reversal without judgment."

**G03**
```html
<h1>Cosa dice la legge</h1><div class="age-bar"><div class="age-fill"></div><span class="age-mark m14">NT(14)</span><span class="age-mark m15">NT(15)</span></div><div class="age-ends"><span>NT(0)</span><span>NT(18)</span></div><div class="ticks"><div class="tick"><span class="tick-mark">⚖️</span><span>Oggi in Italia: sotto i 14 anni serve il consenso dei genitori per iscriversi a un social.</span></div><div class="tick"><span class="tick-mark">👀</span><span>Ma nessuno controlla davvero l'età.</span></div><div class="tick"><span class="tick-mark">🗳️</span><span>Si discute di vietare i social sotto i 15 anni, in Italia e in Europa.</span></div></div>
```
Notes: "Under the Italian privacy code, under-14s may use social media only with explicit parental consent, but nothing verifies it. Several Italian bills are under discussion; a base text in a Senate committee proposes banning accounts for under-15s. At EU level, the proposed KIDS Act would set 15 as the minimum age for an autonomous account, with parent-controlled 'mini accounts' for 13 to 15. France has passed an under-15 ban. Say 'si discute', never 'è legge', unless re-checked."
Verify: `["V: status of the Italian Senate base text and any government bill on a minimum age for social media.", "V: stage of the EU KIDS Act proposal and of the Digital Fairness Act.", "V: the French under-15 law."]`

**G04**
```html
<h1>Cosa dice la scienza</h1><p class="lead">Gli esperti non sono tutti d'accordo su quanto i social facciano male.</p><p class="note strong">Sono d'accordo su:</p><div class="ticks"><div class="tick"><span class="tick-mark">😴</span><span>Il sonno è importante.</span></div><div class="tick"><span class="tick-mark">⚠️</span><span>Alcuni rischi sono reali.</span></div><div class="tick"><span class="tick-mark">🗣️</span><span>Il dialogo aiuta.</span></div></div>
```
Notes: "Psychologist Jonathan Haidt argues social media is a major cause of worse youth mental health; psychologist Candice Odgers argues the evidence shows correlation more than cause, and that teens who already struggle use social media more or differently. Present both fairly: one app will not ruin a child, and it is not 'nothing to worry about' either."

**G05**
```html
<h1>I quattro tipi di rischio</h1><div class="pic-grid"><div class="pic blue"><span class="pic-emoji">👁️</span>Contenuti<small>cosa vedono</small></div><div class="pic orange"><span class="pic-emoji">📩</span>Contatti<small>chi li contatta</small></div><div class="pic purple"><span class="pic-emoji">🧍</span>Comportamenti<small>cosa fanno loro, anche agli altri</small></div><div class="pic green"><span class="pic-emoji">💳</span>Soldi<small>acquisti nelle app, pubblicità, influencer</small></div></div>
```
Notes: "The '4 Cs' of EU Kids Online. Content: violent videos, extreme diet content. Contact: strangers, adults pretending to be peers. Conduct: cyberbullying, sharing photos of others. Commercial: in-game purchases, hidden advertising."

**G06**
```html
<div class="big-emoji">🌙🛏️📵</div><h1>Il sonno prima di tutto</h1><p class="big">Telefoni fuori dalla camera di notte.</p><p class="note strong">Anche per i genitori.</p>
```
Notes: "A household rule limiting phones at night has been linked to lower social media addiction scores and less time on social media in children. Researchers stress that parents should follow the plan too."

**G07**
```html
<h1>Parlare, non solo controllare</h1><div class="ticks"><div class="tick"><span class="tick-mark">💬</span><span class="bubble">Cosa hai visto di divertente oggi?</span></div><div class="tick"><span class="tick-mark">💬</span><span class="bubble">E di strano?</span></div><div class="tick"><span class="tick-mark">💬</span><span class="bubble">Di fastidioso?</span></div></div><div class="handoff"><div class="handoff-title">✍️ In coppia</div><span class="handoff-time">3 minuti</span><p>Scrivete una domanda da fare a vostro figlio questa settimana.</p></div>
```
Notes: "Paediatrician Jenny Radesky suggests asking about the posts they see: funny, strange, creepy, cool, frustrating. Curiosity, not interrogation. If a child mentions something worrying, stay calm, or they stop telling. Activity, 3 min, in pairs."

**G08**
```html
<h1>Un piano di famiglia</h1><div class="pic-grid many"><div class="pic blue"><span class="pic-emoji">🕐</span>Quando</div><div class="pic green"><span class="pic-emoji">📍</span>Dove</div><div class="pic purple"><span class="pic-emoji">⏳</span>Quanto</div><div class="pic orange"><span class="pic-emoji">📱</span>Quali app</div></div><div class="ticks"><div class="tick"><span class="tick-mark">🤝</span><span>Regole decise insieme.</span></div><div class="tick"><span class="tick-mark">📝</span><span>Scritte e appese.</span></div><div class="tick"><span class="tick-mark">👨‍👩‍👧</span><span>Valgono per tutti.</span></div></div>
```
Notes: "The American Academy of Pediatrics recommends a family media plan (healthychildren.org has a free online tool). Rules make sense when children help write them."
Verify: `["V: whether healthychildren.org's family media plan has an Italian version."]`

**G09**
```html
<h1>Gli strumenti dei genitori</h1><div class="ticks"><div class="tick"><span class="tick-mark">🤖</span><span><span class="notranslate" translate="no">Google Family Link</span> (<span class="notranslate" translate="no">Android</span>)</span></div><div class="tick"><span class="tick-mark">📱</span><span>Tempo di utilizzo (<span class="notranslate" translate="no">iPhone</span>)</span></div><div class="tick"><span class="tick-mark">👦</span><span>Account per ragazzi su <span class="notranslate" translate="no">Instagram</span> e <span class="notranslate" translate="no">TikTok</span></span></div></div><p class="note strong">Aiutano. Ma non sostituiscono il dialogo.</p>
```
Notes: "Tools help, but they do not replace the conversation, and teens can get around them. Optionally demo one on the projector."
Verify: `["V: current names and features of Google Family Link, iPhone Screen Time ('Tempo di utilizzo'), Instagram Teen Accounts and TikTok Family Pairing."]`

**G10**
```html
<div class="big-emoji">📱⚠️</div><h1>Sextortion: cos'è</h1><div class="panels"><div class="panel"><span class="panel-n">NT(1)</span><div class="panel-art sm">🎭</div><div class="panel-cap">Un profilo finto, che sembra un ragazzo o una ragazza, chiede foto intime.</div></div><div class="panel"><span class="panel-n">NT(2)</span><div class="panel-art sm">💬</div><div class="panel-cap">Poi minaccia: «Paga o le mando a tutti.»</div></div><div class="panel"><span class="panel-n">NT(3)</span><div class="panel-art sm">⏱️</div><div class="panel-cap">Succede in poche ore.</div></div></div><p class="note strong">Colpisce soprattutto i ragazzi maschi.</p>
```
Notes: "Polizia Postale reports young people contacted by profiles of apparent peers who ask for sexual images and then threaten them. In 2025 it handled 1,225 sextortion cases in Italy, 1,092 with male victims (adults and minors together). Demands often arrive within 24 hours of first contact. AI can now make fake nude images from normal photos, so a child may be blackmailed without ever sending anything. No images of people on this slide, on purpose."
Verify: `["V: Polizia Postale 2025 sextortion figures (1,225 cases, 1,092 male victims)."]`

**G11**
```html
<h1>Sextortion: cosa fare</h1><div class="ticks"><div class="tick"><span class="tick-mark">🚫</span><span>Non pagare.</span></div><div class="tick"><span class="tick-mark">📸</span><span>Non cancellare: fare screenshot.</span></div><div class="tick"><span class="tick-mark">⛔</span><span>Bloccare.</span></div><div class="tick"><span class="tick-mark">🛡️</span><span>Segnalare su <span class="notranslate" translate="no">commissariatodips.it</span>.</span></div><div class="tick"><span class="tick-mark">🤗</span><span>E dire al figlio: «Non sei nei guai. Ti aiuto io.»</span></div></div>
```
Notes: "The most important prevention is telling children, before anything happens, that they can always come to you without being punished. Shame and fear are what offenders count on. Help lines: 114 Emergenza Infanzia, Telefono Azzurro 19696."
Verify: `["V: commissariatodips.it; 114 Emergenza Infanzia; Telefono Azzurro 19696."]`

**G12**
```html
<h1>Segnali da notare</h1><div class="ticks"><div class="tick"><span class="tick-mark">🌧️</span><span>Cambiamenti improvvisi di umore.</span></div><div class="tick"><span class="tick-mark">🚪</span><span>Si chiude, evita il telefono o non lo lascia mai.</span></div><div class="tick"><span class="tick-mark">🕵️</span><span>Account nuovi e segreti.</span></div><div class="tick"><span class="tick-mark">🎁</span><span>Soldi o regali che non si spiegano.</span></div></div>
```
Notes: "Children often signal indirectly, through withdrawal or behaviour changes, rather than by telling. Unexplained gifts, money or new accounts can be signs of grooming (an adult building trust with a child online to abuse or exploit them) or sextortion."

**G13**
```html
<h1>Anche noi pubblichiamo i nostri figli</h1><p class="lead">Prima di pubblicare una foto:</p><div class="ticks"><div class="tick"><span class="tick-mark">🏫</span><span>Si vede la scuola?</span></div><div class="tick"><span class="tick-mark">🏠</span><span>La casa?</span></div><div class="tick"><span class="tick-mark">🧒</span><span>Mio figlio sarebbe d'accordo tra 10 anni?</span></div><div class="tick"><span class="tick-mark">🔒</span><span>Meglio i gruppi privati della famiglia.</span></div></div>
```
Notes: "This is called 'sharenting'. Parents' posts are often a child's first digital footprint. Ties back to slide 7 of the main deck."

**G14**
```html
<h1>Numeri utili</h1><div class="num-grid"><div class="num-card"><span class="num-label">🛡️ Polizia Postale</span><span class="num-big notranslate" translate="no">commissariatodips.it</span></div><div class="num-card"><span class="num-label">🧒 Emergenza Infanzia</span><span class="num-big notranslate" translate="no">114</span></div><div class="num-card"><span class="num-label">💙 Telefono Azzurro</span><span class="num-big notranslate" translate="no">19696</span></div><div class="num-card"><span class="num-label">🚨 Emergenza</span><span class="num-big notranslate" translate="no">112</span></div></div><p class="note strong">📸 Fate una foto a questa slide.</p>
```
Notes: "Suggest a photo of this slide."
Verify: `["V: commissariatodips.it; 114; 19696; 112."]`

### 5.5 `decks.py` changes (WP-C1)

```python
LANG_KEYS = ("it", "en", "fr", "ckb", "kmr", "ar")

def get_raw_slide(slug: str, index: int) -> dict | None
    """The whole slide dict at 1-based index (languages and metadata)."""

def get_slide_meta(slug: str, index: int) -> dict | None
    """{"id": str | None, "notes": str, "verify": list[str], "optional": bool} - teacher only."""
```

`get_slide` keeps its exact behaviour (Italian plus one translation,
never metadata). Add a module docstring paragraph: slides may carry
`id`, `notes`, `verify`, `optional`; only the capture-host endpoints
expose them (ADR 0020).

### 5.6 `/present` changes (WP-C2, `present.html`)

- Add the CSS of 5.2 (prefixed `#local-slide `).
- **Notes panel**, hidden by default because `/present` is what the
  projector shows: a topbar button `Note (N)` (`#notes-btn`, hidden when
  the source is not local) toggles `<aside id="notes" hidden>`: fixed to
  the bottom, 35vh, dark (`#1c1c1c`), scrollable, font 1rem. It shows:
  the slide id and "· facoltativa" when `optional`; each `verify` line in
  a yellow box (`#3a3000` background, `#ffd84d` text); the `notes` text;
  each missing material as a red line "📦 Manca S11-A" plus "(c'è un
  esempio)" when `needed` is `fallback`, linking to `/materiali` in a new
  tab. Key `N` toggles it (add to the keydown switch). All text via
  `textContent`.
- **Missing indicator:** a topbar `<span id="missing">` showing "📦 N"
  when the current local slide has N missing materials, else hidden.
- `loadLocalSlide` already reads the admin endpoint; it now also stores
  `data.id`, `data.notes`, `data.verify`, `data.optional`,
  `data.missing` and calls `renderNotes()`.
- **Setup screen links**, under the two forms: a small block
  "Lezione 8" with links opening in new tabs: `📦 Materiali` →
  `/materiali`, `🎮 Vero o falso?` → `/vero-o-falso`, `🃏 Carte da
  stampare` → `/vero-o-falso/carte`, `🏠 Scheda da stampare` →
  `/games/scheda-social`, `📱 Telecomando con note` →
  `/present/telecomando`.

### 5.7 The phone remote `templates/present_remote.html` (WP-C2)

Standalone, mobile-first, dark like `/present`, no external assets. Polls
`GET /admin/api/live/notes` every 2 s (and right after each button).
Shows:

```
┌─────────────────────────────┐
│ ● Telecomando     12 / 35   │  dot: green ok, red on fetch error
│ S12 · facoltativa           │
│ Lezione: Social media…      │  state.title
│ ┌ VERIFY … (yellow) ──────┐ │
│ └─────────────────────────┘ │
│ Notes text (scrolls)        │
│ 📦 Manca S11-A (red)        │
│ ┌──────────┐ ┌──────────┐   │
│ │  ◀       │ │       ▶  │   │  each ≥ 22vh tall, full half width
│ └──────────┘ └──────────┘   │
│ [ ⏸ Pausa ]  [ 📦 Materiali ] [ 🎮 Gioco ] │
└─────────────────────────────┘
```

◀/▶ → `POST /admin/api/live/goto {"index": index ∓ 1}` (the server
clamps); Pausa → `POST /admin/api/live/status {"status": "blank"|"live"}`.
When no local deck is live: "Nessuna presentazione locale in corso.
Avviala da /present." and the buttons disabled. Text via `textContent`.

---

## 6. Facts to re-check before class (all carried as `verify` flags)

| Slide | What | Why it is flagged |
|---|---|---|
| S06, S08 | WhatsApp menu paths | apps change menus |
| S13 | EC v. TikTok addictive design (DSA) | preliminary finding, outcome pending |
| S15 | PNAS 2026 study on X | figures quoted second-hand |
| S19 | Polizia Postale 2025 figures; FTC 2025 | a 2026 report may be out |
| S23 | FTC romance-scam share | figure quoted second-hand |
| S24, S32, G11, G14 | commissariatodips.it, 112, 114, 19696 | numbers and portals must be right |
| S28 | Chrome's Google Lens menu label | browser versions differ |
| S29 | AI-label wording on platforms | changes often |
| G03 | Italian bill, EU KIDS Act, Digital Fairness Act, French law | legal status changes fast; the slide says "si discute" |
| G08 | Italian version of the family media plan | unknown |
| G09 | Family Link, Screen Time, Teen Accounts, Family Pairing | names and features change |
| G10 | 2025 sextortion figures | quoted second-hand |

The slides attribute numbers to a source and a year (S19) or speak of
debate rather than law (G03). Nothing on screen says "today" about a
fact that is only in the brief. The flags appear in the notes panel and
on the phone remote, in yellow, with the date they were flagged.

---

## 7. The game "Vero o falso?" (WP-D)

### 7.1 Content `vero_o_falso.json` (verbatim; Italian only, WP-T adds languages)

HTML inside `mock` uses **single-quoted attributes** (so the JSON needs no
escaping); `render_slots` accepts both quote styles. Mocks never contain
a working link: link-like text is inside `<span class='blur'>`.
`invented: true` items are always shown with "Esempio creato per il
corso"; any item showing its `mock` because its file is missing is
labelled the same way.

`hardToJudge` decides whether "Devo verificare" earns 1 point on an item
whose answer is something else (brief 4.5: "on any item that is hard to
judge by eye"); it is `false` on the items with clear visible signals (the
scams and the manipulative posts), so "always verify" is not a winning
strategy.

```json
{
 "version": 1,
 "answers": {
  "vero": {"emoji": "✅", "color": "green", "word": {"it": "VERO"}, "sub": {"it": "vero o affidabile"}},
  "falso_ia": {"emoji": "🤖", "color": "red", "word": {"it": "FALSO / IA"}, "sub": {"it": "falso, fatto con l'IA o modificato"}},
  "truffa": {"emoji": "🎣", "color": "yellow", "word": {"it": "TRUFFA"}, "sub": {"it": "vuole soldi o dati"}},
  "verificare": {"emoji": "🔍", "color": "blue", "word": {"it": "DEVO VERIFICARE"}, "sub": {"it": "guardando non si capisce"}}
 },
 "categories": [
  {"id": "foto", "emoji": "📷", "label": {"it": "Foto"}, "items": ["I1", "I2", "I3", "I4"]},
  {"id": "video", "emoji": "🎬", "label": {"it": "Video"}, "items": ["V1", "V2", "V3"]},
  {"id": "voci", "emoji": "🎙️", "label": {"it": "Voci"}, "items": ["A1", "A2"]},
  {"id": "messaggi", "emoji": "💬", "label": {"it": "Messaggi"}, "items": ["M1", "M4", "M2", "M5", "M3"]},
  {"id": "post", "emoji": "📰", "label": {"it": "Post"}, "items": ["P1", "P2", "P3"]},
  {"id": "profili", "emoji": "👤", "label": {"it": "Profili"}, "items": ["F1", "F2", "F3"]}
 ],
 "items": [
  {"id": "I1", "category": "foto", "media": {"type": "image", "slot": "I1"}, "mock": null, "invented": false,
   "caption": {"it": "Mercato del sabato mattina 🍅"}, "answer": "vero", "onlyVerifiable": false, "hardToJudge": true,
   "clue": {"it": "È una foto vera: l'ha fatta l'insegnante con il telefono."},
   "action": {"it": "Chi l'ha pubblicata? Una persona che conosciamo: possiamo chiederle."},
   "source_note": "teacher's own photo", "teachingLink": "S27-Q2"},
  {"id": "I2", "category": "foto", "media": {"type": "image", "slot": "I2"}, "mock": null, "invented": false,
   "caption": {"it": "Mercato del sabato mattina 🍅"}, "answer": "falso_ia", "onlyVerifiable": false, "hardToJudge": true,
   "clue": {"it": "L'ha creata l'IA in pochi secondi. A volte si vedono piccoli errori, ma non sempre."},
   "action": {"it": "Guardare non basta: chiediti da dove viene la foto."},
   "source_note": "AI image made by the teacher", "teachingLink": "S26"},
  {"id": "I3", "category": "foto", "media": {"type": "image", "slot": "I3"}, "mock": null, "invented": false,
   "caption": {"it": "Tramonto di ieri sera 🌅"}, "answer": "vero", "onlyVerifiable": false, "hardToJudge": true,
   "clue": {"it": "Foto vera, senza filtri. Bella non vuol dire falsa."},
   "action": {"it": "Non giudicare dalla bellezza: guarda chi l'ha pubblicata."},
   "source_note": "teacher's own photo", "teachingLink": "S27-Q2"},
  {"id": "I4", "category": "foto", "media": {"type": "image", "slot": "I4"}, "mock": null, "invented": false,
   "caption": {"it": "OGGI in città. Guardate che disastro! 😱 Condividete!"}, "answer": "verificare", "onlyVerifiable": true, "hardToJudge": true,
   "clue": {"it": "La foto è vera, ma è vecchia: «oggi» è falso. Guardando non si può capire."},
   "action": {"it": "Cerca la foto con Google Lens: trovi quando e dove è nata."},
   "source_note": "teacher's own old photo with a false caption", "teachingLink": "S27-Q4"},
  {"id": "V1", "category": "video", "media": {"type": "video", "slot": "V1"}, "mock": null, "invented": false,
   "caption": {"it": "Una passeggiata oggi pomeriggio"}, "answer": "vero", "onlyVerifiable": false, "hardToJudge": true,
   "clue": {"it": "Video vero, fatto con il telefono."},
   "action": {"it": "Chi l'ha pubblicato? Se lo conosci, puoi chiedere."},
   "source_note": "teacher's own video", "teachingLink": "S27-Q2"},
  {"id": "V2", "category": "video", "media": {"type": "video", "slot": "V2"}, "mock": null, "invented": false,
   "caption": {"it": "Guardate che scena incredibile! 😍"}, "answer": "falso_ia", "onlyVerifiable": false, "hardToJudge": true,
   "clue": {"it": "Video creato con l'IA. Oggi questi video sembrano veri."},
   "action": {"it": "Cerca altre fonti: se è vero, ne parlano anche altri."},
   "source_note": "AI video made by the teacher", "teachingLink": "S27-Q3"},
  {"id": "V3", "category": "video", "media": {"type": "video", "slot": "V3"}, "mock": null, "invented": false,
   "caption": {"it": "Ecco cosa succede OGGI in centro! 😱"}, "answer": "verificare", "onlyVerifiable": true, "hardToJudge": true,
   "clue": {"it": "Il video è vero, ma è di un altro giorno o di un altro posto. Guardando non si capisce."},
   "action": {"it": "Dov'è l'originale? Cerca il video prima di condividere."},
   "source_note": "teacher's own video with a misleading caption", "teachingLink": "S27-Q4"},
  {"id": "A1", "category": "voci", "media": {"type": "audio", "slot": "A1"}, "mock": null, "invented": false,
   "caption": {"it": "🎙️ Messaggio vocale"}, "answer": "vero", "onlyVerifiable": false, "hardToJudge": true,
   "clue": {"it": "È la voce vera dell'insegnante, registrata con il telefono."},
   "action": {"it": "Ti chiede aiuto? Richiama la persona al suo numero di sempre."},
   "source_note": "teacher's own voice", "teachingLink": "S22"},
  {"id": "A2", "category": "voci", "media": {"type": "audio", "slot": "A2"}, "mock": null, "invented": false,
   "caption": {"it": "🎙️ Messaggio vocale"}, "answer": "falso_ia", "onlyVerifiable": false, "hardToJudge": true,
   "clue": {"it": "Voce copiata con l'IA da pochi secondi di registrazione. Sembra quasi uguale."},
   "action": {"it": "Chiedi la parola segreta di famiglia. Oppure richiama tu, al numero di sempre."},
   "source_note": "the teacher's own voice cloned with his consent", "teachingLink": "S22"},
  {"id": "M1", "category": "messaggi", "media": {"type": "image", "slot": "M1"},
   "mock": "<div class='mock-phone'><div class='mock-phone-header'><span class='mock-sender'>💬 Numero sconosciuto</span></div><div class='mock-bubble'>Ciao mamma, questo è il mio nuovo numero. Il telefono vecchio si è rotto. Mi serve un favore urgente 🙏</div></div>",
   "invented": false, "caption": {}, "answer": "truffa", "onlyVerifiable": false, "hardToJudge": false,
   "clue": {"it": "Numero nuovo + fretta + presto chiederà soldi: è la truffa «Ciao mamma»."},
   "action": {"it": "Chiama tuo figlio o tua figlia al numero vecchio. Poi blocca e segnala."},
   "source_note": "real redacted screenshot, else invented", "teachingLink": "S20"},
  {"id": "M2", "category": "messaggi", "media": {"type": "image", "slot": "M2"},
   "mock": "<div class='mock-phone'><div class='mock-phone-header'><span class='mock-sender'>✉️ LampoPacchi</span></div><div class='mock-bubble'>Il tuo pacco è fermo in magazzino. Paga 1,99 € entro oggi per la consegna: <span class='blur'>lampopacchi-consegna</span></div></div>",
   "invented": false, "caption": {}, "answer": "truffa", "onlyVerifiable": false, "hardToJudge": false,
   "clue": {"it": "Fretta + un piccolo pagamento + un link: vogliono i dati della carta."},
   "action": {"it": "Non toccare il link. Controlla nell'app o sul sito ufficiale del corriere."},
   "source_note": "real redacted screenshot, else invented (fictional courier)", "teachingLink": "S20"},
  {"id": "M3", "category": "messaggi", "media": {"type": "image", "slot": "M3"},
   "mock": "<div class='mock-phone'><div class='mock-phone-header'><span class='mock-sender'>💬 Numero sconosciuto</span></div><div class='mock-bubble'>Ciao! 😊 Cerchiamo persone per lavoro da casa: metti «mi piace» ai video e guadagni da 50 a 200 € al giorno 💰 Scrivimi su Telegram!</div></div>",
   "invented": false, "caption": {}, "answer": "truffa", "onlyVerifiable": false, "hardToJudge": false,
   "clue": {"it": "Guadagno facile da uno sconosciuto. Prima ti pagano poco, poi ti chiedono soldi."},
   "action": {"it": "Non rispondere. Blocca e segnala."},
   "source_note": "real redacted screenshot, else invented", "teachingLink": "S20"},
  {"id": "M4", "category": "messaggi", "media": {"type": "image", "slot": "M4"},
   "mock": "<div class='mock-phone'><div class='mock-phone-header'><span class='mock-sender'>✉️ LaMiaBanca</span></div><div class='mock-bubble'>Il codice per entrare nell'app è <span class='blur'>482913</span>. Non darlo a nessuno, nemmeno a chi dice di lavorare in banca.</div></div>",
   "invented": false, "caption": {}, "answer": "vero", "onlyVerifiable": false, "hardToJudge": true,
   "clue": {"it": "Messaggio vero: è il codice che hai chiesto tu. Non chiede niente, non ha link."},
   "action": {"it": "Il codice non si dà a nessuno, mai."},
   "source_note": "real legitimate SMS, else invented (fictional bank)", "teachingLink": "S06"},
  {"id": "M5", "category": "messaggi", "media": {"type": "image", "slot": "M5"},
   "mock": "<div class='mock-phone'><div class='mock-phone-header'><span class='mock-sender'>💬 Corso di computer</span></div><div class='mock-bubble'>Ciao a tutte! Giovedì la lezione è alle 16:30, come sempre. Se avete le cuffie, portatele. A giovedì! 😊</div></div>",
   "invented": false, "caption": {}, "answer": "vero", "onlyVerifiable": false, "hardToJudge": true,
   "clue": {"it": "Messaggio vero: un gruppo che conosciamo. Nessuna fretta, nessun soldo, nessun link."},
   "action": {"it": "Hai un dubbio? Chiedi di persona agli operatori."},
   "source_note": "real message shared with permission, else invented", "teachingLink": "S27-Q2"},
  {"id": "P1", "category": "post", "media": {"type": "image", "slot": "P1"}, "mock": null, "invented": false,
   "caption": {}, "answer": "vero", "onlyVerifiable": false, "hardToJudge": true,
   "clue": {"it": "Notizia vera, di un giornale conosciuto. La stessa notizia c'è anche su altri giornali."},
   "action": {"it": "Apri il sito del giornale: trovi la notizia, con la data."},
   "source_note": "real headline with its link", "teachingLink": "S27-Q3"},
  {"id": "P2", "category": "post", "media": null,
   "mock": "<div class='mock-post'><div class='post-head'><span class='post-avatar'>⚡</span><span class='post-page'>Notizie Shock 24<span class='post-meta'>1 ora fa · 🌍</span></span></div><div class='post-body'>VERGOGNA!!! 😡 Il pane costa 5 EURO al chilo!!! Ci stanno RUBANDO tutto!!! CONDIVIDI prima che lo cancellino!!!</div><div class='post-bar'><span>👍 3.412</span><span>💬 1.987</span><span>↗️ 5.230</span></div></div>",
   "invented": true, "caption": {}, "answer": "falso_ia", "onlyVerifiable": false, "hardToJudge": false,
   "clue": {"it": "Parole forti, maiuscole, tanti «!!!» e «condividi prima che lo cancellino»: vuole la nostra rabbia. Nessuna fonte."},
   "action": {"it": "Fermati. Cerca la notizia su un giornale."},
   "source_note": "invented for the course (fictional page)", "teachingLink": "S17"},
  {"id": "P3", "category": "post", "media": null,
   "mock": "<div class='mock-post'><div class='post-head'><span class='post-avatar'>🚗</span><span class='post-page'>Automobilisti Arrabbiati<span class='post-meta'>3 ore fa · 🌍</span></span></div><div class='post-body'>I CICLISTI rovinano la città! 🚲 LORO non pagano niente, NOI paghiamo tutto. Basta! Metti ❤️ se sei d'accordo e condividi!</div><div class='post-bar'><span>❤️ 2.104</span><span>💬 3.560</span><span>↗️ 1.200</span></div></div>",
   "invented": true, "caption": {}, "answer": "falso_ia", "onlyVerifiable": false, "hardToJudge": false,
   "clue": {"it": "«Noi contro loro»: divide le persone in due squadre e cerca la rabbia."},
   "action": {"it": "Non commentare: ogni commento lo fa vedere a più persone."},
   "source_note": "invented for the course (fictional page)", "teachingLink": "S16"},
  {"id": "F1", "category": "profili", "media": {"type": "image", "slot": "F1"}, "mock": null, "invented": false,
   "caption": {}, "answer": "vero", "onlyVerifiable": false, "hardToJudge": true,
   "clue": {"it": "Profilo vero: post da tanti anni, contatti e indirizzo che si possono controllare."},
   "action": {"it": "Controlla sul sito ufficiale: c'è il link allo stesso profilo?"},
   "source_note": "screenshot of a real organisation's profile", "teachingLink": "S27-Q2"},
  {"id": "F2", "category": "profili", "media": null,
   "mock": "<div class='mock-profile'><div class='profile-head'><span class='profile-avatar'><rb-slot data-slot='F2'><span class='profile-avatar-emoji'>👤</span></rb-slot></span><div><div class='profile-name'>Sofia Bellini</div><div class='profile-bio'>💎 Esperta di investimenti</div></div></div><div class='profile-stats'><span class='stat'>📅 Account creato 3 settimane fa</span><span class='stat'>📝 4 post</span><span class='stat'>👥 2.300 amici</span></div><div class='post-body'>Ho guadagnato 5.000 € in un mese! 💰 Scrivimi in privato e ti spiego come.</div></div>",
   "invented": true, "caption": {}, "answer": "falso_ia", "onlyVerifiable": false, "hardToJudge": false,
   "clue": {"it": "Account nuovo, pochi post, tantissimi amici e promesse di soldi: è un profilo falso. Spesso anche la foto è fatta con l'IA."},
   "action": {"it": "Non accettare l'amicizia. Non scrivere. Segnala il profilo."},
   "source_note": "invented for the course (fictional person; optional AI face from slot F2)", "teachingLink": "S17"},
  {"id": "F3", "category": "profili", "media": {"type": "image", "slot": "F3"},
   "mock": "<div class='mock-profile'><div class='profile-head'><span class='profile-avatar'><span class='profile-avatar-emoji'>🏛️</span></span><div><div class='profile-name'>Ufficio Bonus Famiglie ✔️</div><div class='profile-bio'>Pagina ufficiale · Bonus e rimborsi</div></div></div><div class='profile-stats'><span class='stat'>📅 Pagina creata 5 giorni fa</span><span class='stat'>👥 312 follower</span></div><div class='post-body'>Ricevi 500 € di bonus spesa! Scrivi in privato il tuo IBAN e una foto del documento. Solo per oggi! ⏰</div></div>",
   "invented": false, "caption": {}, "answer": "truffa", "onlyVerifiable": false, "hardToJudge": false,
   "clue": {"it": "Una pagina che finge di essere un ufficio: è nuova, ha pochi follower e chiede IBAN e documento in privato. Gli uffici veri non lo fanno."},
   "action": {"it": "Cerca il sito ufficiale dell'ente. Non mandare mai documenti in chat. Segnala la pagina."},
   "source_note": "real public alert screenshot, else invented (fictional office)", "teachingLink": "S20"}
 ],
 "habits": [
  {"emoji": "📲", "it": "Verifica in due passaggi attiva."},
  {"emoji": "🔕", "it": "Notifiche inutili spente."},
  {"emoji": "🤐", "it": "Alla rabbia non rispondo."},
  {"emoji": "⏱️", "it": "Fretta + soldi = mi fermo e chiamo."},
  {"emoji": "🔍", "it": "Prima di condividere: da dove viene?"}
 ],
 "ui": {
  "title": {"it": "Vero o falso?"},
  "subtitle": {"it": "Gioco a squadre"},
  "teams": {"it": "Squadre"},
  "team1": {"it": "Sole ☀️"},
  "team2": {"it": "Luna 🌙"},
  "team3": {"it": "Stelle ⭐"},
  "timer": {"it": "Tempo per pensare"},
  "seconds": {"it": "secondi"},
  "scoring": {"it": "Punti sullo schermo"},
  "scoringOn": {"it": "Sì"},
  "scoringOff": {"it": "No, alla lavagna"},
  "language": {"it": "Lingua"},
  "start": {"it": "Inizia"},
  "resume": {"it": "Riprendi la partita"},
  "newGame": {"it": "Nuova partita"},
  "preparing": {"it": "Preparo foto, video e voci…"},
  "menu": {"it": "Scegli una categoria"},
  "missing": {"it": "Manca il materiale"},
  "fallbackTag": {"it": "Esempio del corso"},
  "invented": {"it": "Esempio creato per il corso"},
  "done": {"it": "Fatto"},
  "think": {"it": "Pensate…"},
  "vote": {"it": "Votate! Alzate un cartoncino."},
  "paused": {"it": "In pausa"},
  "reveal": {"it": "Mostra la risposta"},
  "skip": {"it": "Salta"},
  "next": {"it": "Avanti"},
  "back": {"it": "Rivedi"},
  "clue": {"it": "Indizio"},
  "action": {"it": "Cosa fare"},
  "source": {"it": "Fonte"},
  "categoryDone": {"it": "Categoria finita!"},
  "points": {"it": "punti"},
  "toMenu": {"it": "Torna alle categorie"},
  "finish": {"it": "Fine del gioco"},
  "final": {"it": "Bravissime! Fine del gioco."},
  "habitsTitle": {"it": "Cinque abitudini da portare a casa"},
  "listen": {"it": "Ascolta"},
  "replay": {"it": "Di nuovo"},
  "whoVoted": {"it": "Cosa ha votato ogni squadra?"}
 }
}
```

Counts (tested): 20 items; Foto 4 (2 vero, 1 falso_ia, 1 verificare),
Video 3 (1/1/1), Voci 2 (1 vero, 1 falso_ia), Messaggi 5 (2 vero,
3 truffa), Post 3 (1 vero, 2 falso_ia), Profili 3 (1 vero, 1 falso_ia,
1 truffa); 8 of 20 `vero` = 40%.

Ethics (brief 4.11), all held by this content: the only real person
whose voice may be synthesised is the teacher, with his consent (A2's
instructions); no functional links; invented brands and pages only
(LampoPacchi, LaMiaBanca, Notizie Shock 24, Automobilisti Arrabbiati,
Sofia Bellini, Ufficio Bonus Famiglie); no migration, religion or
nationality topics; invented items labelled; no sound for wrong answers.

### 7.2 `vero_o_falso.py`

```python
GAME_PATH = Path(__file__).parent / "vero_o_falso.json"
ANSWERS = ("vero", "falso_ia", "truffa", "verificare")
LANGS = ("it", "en", "fr", "ar", "ckb", "kmr")
RTL = ("ar", "ckb")
REQUIRED_UI = (...every key of "ui" above...)
ITEM_ID_RE = re.compile(r"^[A-Z][0-9]$")

def load() -> dict                     # functools.lru_cache; tests may call load.cache_clear()
def validate(data: dict) -> list[str]  # [] when valid
def points(item: dict, vote: str) -> int
def points_table(item: dict) -> dict[str, int]   # {answer: points(item, answer) for answer in ANSWERS}
def available_langs(data: dict) -> list[str]     # "it" plus every lang present in ALL ui, answers, labels, clues, actions, habits
def page_config(statuses: dict[str, dict], render_html: Callable[[str], str]) -> dict
def cards_context(copies: int) -> dict
```

**`points`:** `2` if `vote == item["answer"]`; else `1` if
`vote == "verificare" and item["hardToJudge"]`; else `0`. (With
`onlyVerifiable`, the answer is `verificare`, so it earns 2.) No
negative points.

**`validate`:** ids unique and match `ITEM_ID_RE`; every category id
known; the categories' `items` lists cover every item exactly once and
each item's `category` matches; `answer` in `ANSWERS`;
`onlyVerifiable == (answer == "verificare")`; `hardToJudge` is a bool;
`clue["it"]` and `action["it"]` non-empty; every item has `media` or
`mock`; `invented` implies `mock`; `media.type` in image/video/audio;
every `REQUIRED_UI` key has `"it"`; four answers present; five habits.

**`page_config`** returns:

```python
{
  "langs": available_langs(data),
  "langNames": {"it": "Italiano", **i18n.LANGUAGES},
  "rtl": list(RTL),
  "ui": data["ui"],
  "answers": [{"id": a, **data["answers"][a]} for a in ANSWERS],
  "habits": data["habits"],
  "categories": data["categories"],
  "items": [...],                      # below, in categories order
  "defaults": {"timer": 40, "timers": [30, 40, 45, 60], "teams": 2},
  "materialsUrl": "/materiali",
  "storageKey": "rb-vof-v1",
}
```

Each item: `id`, `category`, `answer`, `onlyVerifiable`, `hardToJudge`,
`points` (= `points_table`), `available`, `mediaType`, `mediaUrl`,
`mockHtml`, `invented`, `usesFallback`, `missingSlot`, `caption`,
`clue`, `action`, `link`, `alt`, computed as:

- `slot = item["media"]["slot"]` if `media` else `None`;
  `st = statuses.get(slot)`; `has_file = st and st["file"] and not st["skipped"]`.
- `has_file`: `mediaType = st["file"]["family"]`, `mediaUrl =
  st["file"]["url"]`, `mockHtml = None`, `usesFallback = False`.
- else if `mock`: `mockHtml = render_html(mock)`, `mediaType = None`,
  `usesFallback = slot is not None`.
- else: `available = False`, `missingSlot = slot`.
- `available` is true in the first two cases.
- `invented = item["invented"] or usesFallback`.
- `caption = {"it": st["fields"]["caption"]}` if the teacher set one,
  else `item["caption"]`; `link = st["fields"].get("link")` if `st`.
- `alt` = the Italian caption or the category label.

With no materials at all, the available items are the nine with a mock:
M1-M5, P2, P3, F2, F3. F (not D) passes
`render_html=lambda h: materials.render_slots(h, "admin")` and
`statuses={s["id"]: s for s in materials.all_status()}`.

**`cards_context(copies)`:** `{"copies": min(max(copies, 1), 4),
"langs": [l for l in ("en", "fr", "ar", "ckb", "kmr") if every answer has
word[l]], "rtl": list(RTL), "cards": [{"id", "emoji", "color", "word",
"sub"} for each answer in ANSWERS order]}`.

### 7.3 The game page (`templates/games/vero_o_falso.html` + `game.js`)

Standalone template (like `tutor.html`): context `game_json`, embedded
as `<script id="vof-config" type="application/json">{{ game_json | safe }}</script>`,
then `<script src="/static/lessons/lezione-8/vero-o-falso/game.js?v={{ static_version }}"></script>`.
It includes `games/_vof_icons.html` (a Jinja macro file with the four
icons, also used by the cards page) inside hidden
`<template id="icon-vero">`… elements that `game.js` clones.

**Icons** (inline SVG, `viewBox="0 0 100 100"`, `fill="none"`,
`stroke="currentColor"`, `stroke-width="10"`, `stroke-linecap="round"`,
`stroke-linejoin="round"`):

- vero (check): `<polyline points="18,54 42,76 84,26"/>`
- falso_ia (robot): `<rect x="20" y="32" width="60" height="48" rx="10"/><circle cx="38" cy="54" r="5" fill="currentColor"/><circle cx="62" cy="54" r="5" fill="currentColor"/><line x1="38" y1="68" x2="62" y2="68"/><line x1="50" y1="32" x2="50" y2="16"/><circle cx="50" cy="12" r="4" fill="currentColor"/>`
- truffa (hook): `<circle cx="62" cy="12" r="6"/><path d="M62 18 V62 A20 20 0 0 1 22 62 V50"/><path d="M22 50 L14 62 M22 50 L30 62"/>`
- verificare (magnifier): `<circle cx="42" cy="42" r="26"/><line x1="61" y1="61" x2="86" y2="86"/>`

**Look:** dark navy background `#14213d`, white text, base
`font-size: max(24px, 2vw)` (at least 32 px on a 1080p projector),
headings larger. Answer colours with their word and icon, never colour
alone: green `#1e7a3c` (white text), red `#b42318` (white), yellow
`#f5b800` (text `#1b1f24`), blue `#1a56c4` (white). It defines its own
copies of `.mock-phone`, `.mock-phone-header`, `.mock-sender`,
`.mock-bubble`, `.mock-post` and children (5.2), `.blur { filter:
blur(5px); }`, and the profile mock:

```css
.mock-profile { max-width: 26rem; margin: 0 auto; background: #fff; color: #111; border-radius: 14px; padding: 0.8rem 1rem; text-align: start; }
.profile-head { display: flex; gap: 0.8rem; align-items: center; }
.profile-avatar { width: 4.5rem; height: 4.5rem; border-radius: 50%; overflow: hidden; background: #e8f0fe; display: flex; align-items: center; justify-content: center; flex: 0 0 auto; }
.profile-avatar img { width: 100%; height: 100%; object-fit: cover; border-radius: 50%; box-shadow: none; max-height: none; }
.profile-avatar .slot-media { margin: 0; }
.profile-avatar-emoji { font-size: 2.6rem; }
.profile-name { font-weight: 800; font-size: 1.2em; }
.profile-bio { color: #555; font-size: 0.85em; }
.profile-stats { display: flex; flex-wrap: wrap; gap: 0.4rem 1rem; margin: 0.6rem 0; font-size: 0.85em; color: #333; }
```

All page text comes from `ui` (with `langs`); only `mockHtml` (server
HTML from committed JSON, with any teacher text already escaped by
`render_slots`) is set with `innerHTML`. Teacher captions and links use
`textContent`; the P1 link is an `<a target="_blank" rel="noopener">`
whose `href` is set only if it starts with `https://` or `http://`.
Bilingual text: Italian line, then a smaller second line in the chosen
language (`lang`, `dir="rtl"` for `ar`/`ckb`) when one is chosen and
present.

**State** (memory; mirrored to `localStorage[storageKey]` after every
change, inside try/catch; never anything about students):
`{teams: [{name}], timer, scoring, lang, include: {id: bool}, votes:
{id: {teamIndex: answer}}, done: {id: true}, screen, cat, pos}`. Scores
are always recomputed as `sum(item.points[vote])` over `votes`, so they
are idempotent.

**Screens:**

1. **Start.** Title and subtitle; if saved state exists: "Riprendi la
   partita" / "Nuova partita". Team count 2 or 3 (segmented), team name
   inputs (defaults `team1`-`team3`), timer 30/40/45/60 (default 40),
   "Punti sullo schermo" Sì / No (alla lavagna), language buttons for
   `langs` (Italiano only = default). A box listing unavailable items
   ("📦 Manca il materiale: I1, V2 … ➜ /materiali", link in a new tab) and
   fallback ones ("🧪 Esempio del corso: M2, F3"). "Inizia" → preload:
   for every available item with `mediaUrl`, `fetch` → `blob` →
   `URL.createObjectURL`, progress "Preparo foto, video e voci… 7 / 12";
   a failed fetch keeps the original URL and lists the id. Then Menu.
2. **Menu.** Six tiles (emoji, label, "2 / 4 fatti"). Under each tile its
   items as chips: id plus ✓ (done), 📦 (unavailable, disabled), 🧪
   (fallback); a chip toggles `include`. Tapping a tile plays its included,
   available, not-done items in order. "🏁 Fine del gioco" → Final.
3. **Item.** Top bar: category, "2 / 4", the countdown (big number;
   "⏸ In pausa"; at 0 "🗳️ Votate! Alzate un cartoncino."), language, 🔈.
   Middle: the caption as a post caption; then the media, large: image
   (`max-height: 58vh`), video (plays once automatically, then a big
   "↻ Di nuovo"), audio (a round ▶ "Ascolta" button 30vh wide, then
   "↻ Di nuovo"), or the mock. Bottom: the four answer reminders (icon +
   word + colour). If scoring: one row per team, its name and four small
   answer buttons (`aria-pressed`); a team can change its vote until the
   reveal. Buttons "⏸ Pausa", "Mostra la risposta", "Salta".
4. **Reveal.** A big answer panel (colour, icon, word, `sub`), the
   media small again, "💡 Indizio: …", "👉 Cosa fare: …" (bilingual),
   "Esempio creato per il corso" if `invented`, "Fonte: <link>" if `link`.
   A gentle chime (Web Audio: sine 660 Hz then 880 Hz, 0.15 s each,
   gain 0.08; off with the 🔈 toggle). No per-team results here (nobody
   is exposed). Buttons "← Rivedi" (back to the item, timer stopped) and
   "Avanti →".
5. **Category end.** "Categoria finita! 🎉"; if scoring, each team's total
   in team order with a bar; "Torna alle categorie".
6. **Final.** Totals (if scoring), then "Cinque abitudini da portare a
   casa" (the five habits, large). "Nuova partita" clears the saved state.

**Keys:** Space = pause/resume the countdown (item); R or → = reveal
(item: the reveal is never skipped by →); → or Enter = next (reveal);
← = back to the item (reveal); S = skip the item without reveal (item);
P = play/replay media; M = menu; F = fullscreen
(`document.documentElement.requestFullscreen()`); L = next language;
ignore keys while focus is in an input.

No network call except loading the page, `game.js` and the media
(preloaded). No sound for wrong answers. No `eval`, no external assets.

### 7.4 The answer cards (`templates/games/vero_o_falso_carte.html`)

Context from `cards_context(copies)`. Screen: a toolbar (hidden in print)
with "🖨️ Stampa", "Copie" 1-4 (a link reloading with `?copie=N`) and
"Stampa su A4, una carta per pagina." Print: `@page { size: A4 portrait;
margin: 0; }`, one card per page (`break-after: page`), the set repeated
`copies` times. Each card: full-page background in the answer colour
(with `print-color-adjust: exact; -webkit-print-color-adjust: exact;`),
a white circle with the icon at 9 cm, the Italian word at 80 pt bold,
`sub` at 24 pt, then each language in `langs`: word at 36 pt and `sub` at
18 pt (`dir="rtl"` for ar/ckb). Colour is never the only signal.

---

## 8. Take-home card (WP-E)

### 8.1 `scheda_social.json` (verbatim; WP-T adds languages)

```json
{
 "title": {"it": "Social media: la scheda da portare a casa"},
 "side1": {
  "title": {"it": "Prima di credere o condividere"},
  "questionsTitle": {"it": "Quattro domande"},
  "questions": [
   {"emoji": "✋", "it": "Fermati."},
   {"emoji": "👤", "it": "Chi l'ha pubblicato?"},
   {"emoji": "📰", "it": "Cosa dicono altre fonti?"},
   {"emoji": "🔍", "it": "Dov'è l'originale?"}
  ],
  "signalsTitle": {"it": "Tre segnali di truffa"},
  "signals": [
   {"emoji": "⏱️", "it": "Fretta: «Subito!»"},
   {"emoji": "💓", "it": "Un'emozione forte: paura, amore, guadagno facile."},
   {"emoji": "🔒", "it": "Un pagamento strano o segreto."}
  ],
  "rule": {"it": "Fretta + soldi = mi fermo e chiamo."}
 },
 "side2": {
  "title": {"it": "Numeri utili"},
  "numbers": [
   {"emoji": "🛡️", "label": {"it": "Polizia Postale"}, "value": "commissariatodips.it"},
   {"emoji": "🚨", "label": {"it": "Emergenza"}, "value": "112"},
   {"emoji": "🧒", "label": {"it": "Emergenza Infanzia"}, "value": "114"},
   {"emoji": "💙", "label": {"it": "Telefono Azzurro"}, "value": "19696"}
  ],
  "bank": {"it": "La mia banca:"}
 },
 "ui": {
  "print": {"it": "🖨️ Stampa"},
  "howto": {"it": "Stampa fronte e retro, sul lato corto. Poi taglia a metà: due schede."}
 }
}
```

Each `{"it": ...}` object (and each `questions`/`signals` entry) gains
language keys from WP-T. `value` strings are never translated.

### 8.2 `scheda_social.py`

```python
def load() -> dict                      # lru_cache
def langs() -> list[str]                # "it" plus languages present on every string
def context(lang: str) -> dict          # {"c": load(), "lang": lang if lang in langs() else "it",
                                        #  "second": lang != "it" and lang in langs(), "rtl": lang in ("ar", "ckb")}
```

### 8.3 `templates/games/scheda_social.html`

Standalone. On screen: the toolbar (`ui.print`, `ui.howto`, hidden in
print) and a preview. Print: `@page { size: A4 landscape; margin: 8mm; }`;
page 1 has two identical A5 halves of side 1 side by side, page 2 two of
side 2, separated by a dashed cut line. Side 1: title, the four questions
(emoji, Italian, second-language line under it when `second`), the three
signals, the rule in bold. Side 2: title, the four numbers (emoji, label,
value large, `dir="ltr"` on values), and "La mia banca:" followed by a
long writing line. Black on white except thin coloured accents. Second
language lines use `lang` and `dir`.

---

## 9. Routes and wiring (`main.py`, WP-F)

**Imports:** add `hmac`, `from fastapi.responses import FileResponse`,
`from starlette.concurrency import run_in_threadpool`, and
`materials, scheda_social, vero_o_falso` to the sorted
`rev_babel_web` import.

**Lesson entries:**

```python
LESSONS += {"slug": "lezione-8", "title": "Lezione 8", "long_title": "I social network", "url": "/course/lezione-8"}
# The take-home card: a printable page, its own tab, no score (ADR 0020).
LESSON8_GAMES = {"scheda": {"title": "Scheda da portare a casa", "unit": "s", "max_value": 3_600,
                            "src": "/games/scheda-social", "new_tab": True}}
LESSON_GAMES["lezione-8"] = LESSON8_GAMES   # not added to GAMES (no score)
```

(Write the lesson dict inside the `LESSONS` literal and the entry inside
the `LESSON_GAMES` literal, like lessons 6 and 7.) The decks need no
registration: `decks.list_decks()` finds them.

**Key gate:**

```python
# Lesson 8's materials page writes what students see, so on top of the
# capture-host gate it honours an optional key (ADR 0020).
MATERIALS_KEY = os.environ.get("MATERIALS_KEY", "")

def _materials_ok(request: Request) -> bool:
    return not MATERIALS_KEY or bool(request.session.get("materials_ok"))

def _require_materials_access(request: Request) -> None:
    _require_capture_host(request)
    if not _materials_ok(request):
        raise HTTPException(status_code=401, detail="Serve la chiave dei materiali.")
```

Read `MATERIALS_KEY` through the module global at call time so tests can
monkeypatch it. Compare keys with `hmac.compare_digest`.

**Models:** `MaterialFieldsIn(fields: dict[str, str] = Field(max_length=10))`,
`MaterialSkipIn(skipped: bool)`, `MaterialDeleteAllIn(confirm: str)`.
Every `materials.MaterialError` becomes
`HTTPException(exc.status, detail=exc.message)`.

**Routes** (all new ones on the capture host unless said):

| Route | Behaviour |
|---|---|
| `GET /materiali` (`k` query optional) | host gate. If `k` is given and a key is configured: match → `session["materials_ok"] = True`, 303 to `/materiali` (drops the key from the address bar); no match → page with `needs_key=True, key_error=True`. Else `needs_key = not _materials_ok`. Render `materials.html` with `needs_key`, `key_error`, `key_configured=bool(MATERIALS_KEY)`. |
| `POST /materiali/chiave` (form `key`) | host gate; same check; 303 or the form with the error. |
| `GET /admin/api/materials` | `_require_materials_access`; `{**materials.page_data(), "keyConfigured": bool(MATERIALS_KEY)}` |
| `POST /admin/api/materials/{slot_id}/file` | `async def`; `_require_materials_access`; 404 if `materials.slot` is `None`; 413 if `Content-Length` > `limit_for`; stream `request.stream()` into `materials.new_tmp_path()` counting bytes, 413 past the cap; 400 "File vuoto." if 0 bytes; `await run_in_threadpool(materials.store_upload, slot_id, tmp)`; always `tmp.unlink(missing_ok=True)` in `finally`; return the status. |
| `DELETE /admin/api/materials/{slot_id}/file` | access; `materials.delete_file` |
| `POST /admin/api/materials/{slot_id}/fields` | access; `materials.set_fields(slot_id, body.fields)` |
| `POST /admin/api/materials/{slot_id}/skip` | access; `materials.set_skipped(slot_id, body.skipped)` |
| `POST /admin/api/materials/delete-all` | access; 400 unless `confirm == "ELIMINA"`; `materials.delete_all()`; `{"ok": true}` |
| `GET /admin/materials/{slot_id}/file` | host gate only (no key, so `/present` and the game work on the classroom PC); `materials.file_for` or 404; `FileResponse(path, media_type=mime, headers={"Cache-Control": "private, max-age=86400", "X-Content-Type-Options": "nosniff"})` |
| `GET /api/live/material/{slot_id}` (**student host**) | 401 without login; 404 unless the live state is `source == "local"`, `status == "live"`, and `slot_id` is in `materials.slots_in_html` of the joined language strings of `decks.get_raw_slide(deck_slug, index)` (keys in `decks.LANG_KEYS`); 404 if skipped or no file; else the `FileResponse` with `Cache-Control: private, max-age=3600` and `nosniff` |
| `GET /admin/api/decks/{slug}/slides/{index}` (changed) | as now, plus `it` passed through `render_slots(..., "admin")`, plus `**decks.get_slide_meta(...)` and `"missing": _slide_missing(slug, index)` |
| `GET /api/live/slide` (changed) | as now, both `it` and `translated` passed through `render_slots(..., "student")`; still no metadata |
| `GET /admin/api/live/notes` | host gate; `{"state": live.get_state(), "slide": meta + missing, or null}` for a live local deck |
| `GET /present/telecomando` | host gate; `present_remote.html` |
| `GET /vero-o-falso` | host gate; `game_json` = `json.dumps(vero_o_falso.page_config(statuses, render), ensure_ascii=False).replace("</", "<\\/")`; `games/vero_o_falso.html` |
| `GET /vero-o-falso/carte` (`copie: int = 3`) | host gate; `vero_o_falso.cards_context(copie)` → `games/vero_o_falso_carte.html` |
| `GET /games/scheda-social` (`lang` query optional) | on the capture host: no login, `lang` from the query (`it` if absent or unknown); elsewhere: 303 to `/` without login, the student's own language; `scheda_social.context(lang)` → `games/scheda_social.html` |

`_slide_missing(slug, index)` = for each slot id in the Italian slide
(sorted): include `{"id", "needed"}` when its status has no file or is
skipped. With `CAPTURE_HOST` unset (development) the host gate lets
everything through, exactly like `/present` today; on the capture host
the scheda route treats the request as the teacher's.

**`.env.example`** gains, after the Anthropic block:

```
# Lesson 8 materials page (/materiali on the capture host). Optional but
# recommended: when set, the page asks for this key once per session (or
# open /materiali?k=<key> from a bookmark). Leave empty to rely on the
# capture-host gate alone (ADR 0020).
MATERIALS_KEY=
```

---

## 10. ADR 0020 and the privacy doc (WP-G)

### 10.1 Create `docs/decisions/0020-lesson-8-materials-store-and-game.md`

```markdown
# 0020. Lesson 8: a teacher-only materials store, presenter notes, and a projector game

- **Status:** accepted
- **Date:** 2026-11-16

## Context

Lesson 8 is about social media: how feeds work, scams, fakes made with
AI. It teaches best with real examples: the teacher's own photo next to
an AI image of the same scene, a real "Ciao mamma" scam screenshot with
the number covered, the teacher's own voice and a clone of it. For
example, the class sees two pictures of a market stall and votes which
one is real; one was taken on the teacher's phone last Saturday.

Until now everything a deck showed was HTML committed to this public
repository, and the repository must never hold a photograph or a
recording (`docs/data-and-privacy.md`). Phone photos and videos also
carry hidden data, including GPS coordinates of where they were taken.
The teacher wants to provide this material himself, easily, from his
phone, deck by deck, without touching the repository.

The lesson also has a team game ("Vero o falso?") played on a projector,
and the brief asks for presenter notes with dated "verify before class"
flags on fast-changing facts.

## Decision

**Materials live outside git.** A committed manifest
(`rev_babel_web/materials_manifest.json`) lists every "slot" a deck or
the game can use, with instructions for the teacher. The files
themselves are stored in `data/materials/<slot>/` on the teacher's
machine (gitignored, with an explicit line), one cleaned file plus a
small `meta.json` per slot. The original file name is not kept.

**Only the teacher can provide them.** The materials page
(`/materiali`) and its API exist only on the capture host, like
`/present` (ADR 0014). Because this is write access to what students
see, the page also honours an optional `MATERIALS_KEY` (asked once per
session, or carried by a bookmarked `?k=` link). Without the key, the
exposure is the same accepted risk as ADR 0014 and issue 0001, now
including "someone who finds the address could put an image in front of
the class"; the page says so.

**Hidden data is removed.** The page re-encodes every image in the
browser through a canvas, which drops EXIF, GPS and XMP and applies the
rotation. The server then identifies each file by its first bytes and
strips metadata with the standard library only: JPEG APP/COM segments
(keeping JFIF, the colour profile and Adobe), PNG text, time and EXIF
chunks, WebP EXIF/XMP, the `udta`/`meta`/`uuid` boxes of MP4/MOV/M4A
(where phones store the location; overwritten in place as empty `free`
boxes so the video still plays), MP3 ID3 tags and non-audio WAV chunks.
HEIC and unknown types are refused; sizes are capped (15 MB images,
20 MB audio, 90 MB video, 2 GB in all). Pillow was not added: one lesson
does not justify a new compiled dependency when the browser already
re-encodes.

**Students see a file only while it is on screen.** On the student host a
file is served only through `/api/live/material/<slot>`, to a logged-in
student, while the live local slide contains that slot. Game media are
served on the capture host only.

**Missing material degrades visibly.** A deck marks a spot with
`<rb-slot data-slot="...">`; the server renders the file, or a drawn
example labelled "Esempio creato per il corso", or a "📦 Materiale in
arrivo" box. A game item without its file uses its drawn example or is
skipped and flagged for the teacher.

**Presenter notes stay with the teacher.** Deck slides may carry `id`,
`notes`, `verify` and `optional`. Only capture-host endpoints return
them: a hidden-by-default panel on `/present` (which the projector
shows) and a phone remote at `/present/telecomando`.

**The game is driven by the teacher on the projector** (`/vero-o-falso`,
capture host). Teams vote with paper cards; the teacher may record votes
for on-screen scoring. State lives in the page and in that browser's
`localStorage` (team names and points; nothing about any student). No
shared state, no student data, no network beyond loading the page and
its media, which it preloads.

**Retention.** Materials stay until the teacher deletes them, one by one
or with "Elimina tutto" on the page. Recordings of the teacher's voice
(the real one and the AI copy) are deleted after the lesson, and the copy
is deleted from the cloning service right after it is made; the whole
store is deleted at the end of the course.

## Consequences

The machine now holds, outside git, the teacher's own photos and videos
of everyday scenes without faces, screenshots with numbers covered, and
two recordings of the teacher's voice: a new category of data, described
in `docs/data-and-privacy.md`. None of it is a student's, and none of it
reaches the repository, logs or fixtures; tests build their images and
videos from bytes.

Easier: the teacher provides material from his phone with no repository
step, the decks and the game work before anything arrives, and notes
with dated flags reach him without reaching students. Harder: more
surface on the unprotected capture host (issue 0001 is more urgent
still); the cleaner is home-made and covers the common formats only
(Ogg and WebM pass unchanged, as browser and messaging recordings carry
no location); a slide with missing material on the day shows a
placeholder.

Not verified at the time of writing: the materials page, the game and
the notes panel in a real browser or on a phone (this machine has none),
the in-page recorder, canvas re-encoding of iPhone photos, and uploads of
large videos through the tunnel.
```

### 10.2 `docs/data-and-privacy.md`

Under **What is stored, where, for how long**, after the Python page
bullet, add:

```markdown
- **Lesson 8 materials** (`/materiali` on the capture host,
  [ADR 0020](decisions/0020-lesson-8-materials-store-and-game.md)) -
  files the **teacher** provides for the lesson 8 decks and game: his own
  photos and short videos of everyday scenes with no faces, images and
  videos he generated with AI, real scam screenshots with numbers, names
  and links covered, a public news headline, and two recordings of his
  own voice (one real, one an AI copy he made with his consent). Stored in
  `data/materials/` on his machine, never in git; hidden data (GPS, EXIF)
  is removed on upload; the original file name is not kept. Shown on the
  capture host, and to a logged-in student only while the slide that
  uses it is live. Kept until he deletes them (one by one, or "Elimina
  tutto"); the voice recordings are deleted after the lesson and the
  whole store at the end of the course. Never a student's photo, voice
  or message.
- **Lesson 8 game** (`/vero-o-falso`) - runs in the teacher's browser on
  the projector. It keeps team names and points in that browser's
  `localStorage` only. Nothing about any student is entered or stored.
```

Under **What is deliberately not stored**, change the first bullet to:

```markdown
- No recordings of any kind, of anyone, beyond what a fallback mechanism
  requires transiently (if any — TODO, see `operations.md`), **except**
  the teacher's own voice for lesson 8's game (ADR 0020), which he records
  and deletes himself. Never a student's or the assistant's voice.
```

and append to the photograph bullet: "Lesson 8's materials store
(ADR 0020) holds the teacher's own photos of everyday scenes, without
faces, on his machine only; never a student's."

In **Repository rules**, change the `.gitignore` sentence to list
`data/` (including `data/materials/`), and add a bullet:

```markdown
- **Lesson 8 materials are never committed**, not even as fixtures:
  tests build images, videos and audio from bytes. Every committed
  lesson 8 file uses "il corso" / "gli operatori" / "l'insegnante": no
  provider, venue, city, teacher or assistant name.
```

### 10.3 Other docs (WP-G)

- `docs/architecture.md`: after the Pyodide sentence, add "Lesson 8's
  materials (teacher-provided photos, videos, voice) live in
  `data/materials/`, uploaded only on the capture host and cleaned of
  metadata on upload (ADR 0020)."
- `data/README.md`: add `materials/` to the list: "lesson 8's
  teacher-provided materials (ADR 0020), managed from `/materiali`".
- `apps/web/static/README.md`: `lessons/lezione-8/materiali/materiali.js`
  (the teacher's materials page: canvas re-encoding, recorder, uploads;
  no storage APIs) and `lessons/lezione-8/vero-o-falso/game.js` (the
  projector game; keeps team names and points in `localStorage` on the
  teacher's browser only).
- `apps/web/templates/README.md`: replace "Placeholder…" with one line
  per standalone page added since: `games/*.html` are full-window pages;
  `present.html`, `present_remote.html` and `materials.html` are
  capture-host only.

F updates `apps/web/README.md` (a "**Lesson 8**" paragraph: two decks
with notes, `/materiali`, `/vero-o-falso`, the card, ADR 0020) and
`ROADMAP.md` ("Where we are now" dated, first bullet on lesson 8 with
what was verified and what was not; revision log **v0.21 - <date>**).

---

## 11. Translations (WP-T, skippable)

### 11.1 `scripts/translate_content.py`

```
scripts/translate_content.py --all [--langs en,fr,ckb,kmr,ar] [--force] [--dry-run]
scripts/translate_content.py --export-csv data/lezione8.csv
scripts/translate_content.py --import-csv data/lezione8.csv
```

- Imports `api_code`, `load_key`, `translate` from `scripts/translate.py`
  by path (`importlib`), so the key handling stays in one place (header,
  never the URL; `.env` or environment; exits if missing).
- **Units:** every deck slide's `it` (format `html`; the result goes in
  the slide's language key); in `vero_o_falso.json` every `{"it": ...}`
  object (`caption`, `clue`, `action`, category `label`, answer `word`
  and `sub`, `habits` entries, `ui`) in format `text`; every
  `{"it": ...}` in `scheda_social.json` in format `text`. The game's
  `mock` HTML is **not** translated: those are messages as they arrive on
  a phone in Italy. Ids: `deck:<slug>:<slide id>`, `game:<json path>`,
  `scheda:<json path>`.
- **Only missing** translations by default; `--force` redoes them.
  `--dry-run` prints the unit count and characters per language, sends
  nothing.
- **Validation (HTML units):** the translation must have the same tag
  signature as the Italian (the ordered list of tag names with their
  `class`, `data-slot`, `data-field` and `translate` attributes, via
  `html.parser`), the same `<rb-slot>` ids, and every
  `translate="no"` span's text unchanged. On failure the unit is left
  untranslated and reported; the run continues.
- Writes JSON with `ensure_ascii=False, indent=1` and a top-level
  `"translation": {"by": "Google Cloud Translation", "reviewed": false,
  "date": "<today>"}` in each file it changed.
- **UI strings:** adds `"I social network"` and `"Scheda da portare a
  casa"` to `strings.json` for every language (hover titles).
- **CSV:** export writes `id,it,en,fr,ckb,kmr,ar` for every unit
  (UTF-8 with BOM so a spreadsheet opens it right); import reads it back,
  validates as above, and writes only changed cells. CSV files go
  wherever the maintainer says (suggest `data/`, gitignored).
- Prints, at the end: "Machine translation, unreviewed: ask a native
  speaker to check before relying on it."

### 11.2 Running it

1. `python3 -I scripts/translate_content.py --all --dry-run` (sends
   nothing).
2. If the key is configured: `python3 -I scripts/translate_content.py --all`.
   If it exits with "GOOGLE_TRANSLATE_API_KEY is not set", stop: commit
   the script and its tests only, and tell the lead "lesson 8 ships
   Italian only".
3. `make test` (the deck, game and card tests must still pass with the
   new keys).

### 11.3 `test_translate_content.py` (no network)

Load the script by path. With a fake `translate` (returns `"[xx] " +
text` for text, and for HTML wraps text nodes the same way): units are
collected from fixture dicts; a correct HTML translation is accepted; one
that drops a tag, changes an `rb-slot` id or alters a `translate="no"`
span is rejected; `--force` off keeps existing translations; CSV export
then import round-trips; metadata keys (`id`, `notes`, `verify`,
`optional`) are never sent.

---

## 12. Tests, acceptance, verification

All tests are Python, run by `make test`; fixtures are invented bytes
and role labels, never a real photo or voice. `DATA_DIR` is already a
temp dir in `conftest.py`; `materials.MATERIALS_DIR` derives from it.

### 12.1 Per package

**WP-A** - `test_media_clean.py`:
1. `sniff` table: each magic in 4.5 gives the right triple; HEIC and
   AVIF brands raise `Unsupported` mentioning HEIC; random bytes raise.
2. JPEG built from bytes (SOI, APP0 JFIF, APP1 `Exif\0\0` + "GPS",
   APP2 ICC, COM, a tiny DQT, SOS + data, EOI): APP1 and COM gone, APP0,
   APP2 and everything from SOS on unchanged; truncated segment raises.
3. PNG built with `zlib`/`struct` (IHDR, tEXt, eXIf, IDAT, tIME, IEND):
   only IHDR, IDAT, IEND left, in order, CRCs untouched.
4. WebP (`VP8X` with EXIF and XMP flags, `VP8 `, `EXIF`, `XMP `): chunks
   gone, flags cleared, RIFF size right.
5. MP4 written to a temp file (`ftyp`, `moov`[`mvhd`, `udta`[`©xyz`],
   `trak`[`tkhd`, `meta`]], `mdat`, top-level `uuid`): after
   `neutralise_mp4`, `udta`, `meta`, `uuid` are `free` with zero
   payload, file size unchanged, `mvhd`, `tkhd`, `mdat` bytes unchanged;
   a box with a size past the end raises.
6. MP3 with ID3v2 (+ footer flag) and ID3v1: both removed, starts with a
   frame sync. WAV with `LIST`: removed, RIFF size right.

**WP-A** - `test_materials.py`:
7. `validate_manifest(manifest()) == []`; a broken copy (duplicate id,
   bad kind, game slot without answer, unknown artifact) gives errors.
8. Status transitions: mancante → pronto (file, no required fields) →
   saltato → pronto (unskip) → mancante (delete); P1 with file and no
   link is `incompleto`, with a link `pronto`.
9. `store_upload` with a PNG for an `audio` slot → 415; over the limit
   (monkeypatch `LIMITS`) → 413; replacing a `.jpg` with a `.png` leaves
   one file; `version` changes; `meta.json` has no file name.
10. `set_fields`: unknown key, too long, `javascript:` link → errors;
    empty string removes.
11. `render_slots`: missing without inner → the 📦 box; missing with
    inner → the inner; image/video/audio with the right URL per audience;
    a field with `<script>` is escaped; the `data-field` default shows when
    unset; single-quoted attributes work.
12. `delete_all` empties the store; nothing is ever written outside
    `MATERIALS_DIR`.

**WP-C1** - `test_lesson8_decks.py`:
13. Both decks listed with 35 and 14 slides and the titles of 5.1.
14. Ids exactly in the order of 5.3/5.4; every slide has non-empty `it`
    and `notes`; `S08` and `S29` are `optional`; the slides named in
    section 6 carry `verify` lines starting with "VERIFY before class".
15. No `{{ROUTE`, no `NT(` left; every `<rb-slot` matches `SLOT_TAG_RE`
    (copy the pattern into the test); tags are balanced (an
    `html.parser` walk, void elements excepted).
16. `get_slide` never returns `notes`/`verify`; `get_slide_meta` and
    `get_raw_slide` work and are `None` out of range.
17. Word budget: the visible Italian text of each slide is at most 60
    words, except `S18` and `S18b` (three posts to read, about 90).

**WP-D** - `test_vero_o_falso.py`:
18. `validate(load()) == []`; counts and mix of 7.1 (per category and 8
    of 20 `vero`).
19. `points`: correct → 2; `verificare` on a `hardToJudge` item → 1; on
    others → 0; on an `onlyVerifiable` item → 2; never negative.
20. `page_config` with no statuses: available = M1-M5, P2, P3, F2, F3;
    I1 unavailable with `missingSlot == "I1"`; fallback items `invented`.
21. With a fake status for I1 (file present): available, `mediaUrl` from
    the status, caption overridden by a teacher caption; a skipped M1
    falls back to its mock; a fake `render_html` is applied to mocks.
22. No mock contains `href`, `http`, `www.` or a `<script`; every mock
    with link-like text uses `blur`.
23. `cards_context(9)["copies"] == 4`; four cards in order.

**WP-E** - `test_scheda_social.py`:
24. Every text has `it`; the four numbers are exactly
    `commissariatodips.it`, `112`, `114`, `19696`; `context("ar")` with
    no Arabic yet falls back to `it` with `second` false.

**WP-F** - `test_lesson8_routes.py` (headers `{"Host": "mic.test"}` for
the capture host, logged-in clients via `/welcome` with role-label names
such as `student_a`):
25. `/course/lezione-8` lists "Scheda da portare a casa" and "Segui la
    lezione"; the course sidebar shows "I social network".
26. Off the capture host, 403 for: `/materiali`, `/admin/api/materials`,
    each materials POST/DELETE, `/admin/materials/I1/file`,
    `/vero-o-falso`, `/vero-o-falso/carte`, `/present/telecomando`,
    `/admin/api/live/notes`.
27. On the host: `/materiali` 200; `/admin/api/materials` lists every
    manifest slot, all `mancante`; the parents' artifact has
    `nothingNeeded`.
28. Upload a PNG with a `tEXt` chunk to `S11-A` (raw body) → `pronto`;
    `GET /admin/materials/S11-A/file` returns it without `tEXt`, with
    `nosniff`; upload `b"hello"` → 415; HEIC-like bytes → 415 with
    "HEIC"; a `Content-Length` over the cap → 413; unknown slot or
    `..%2F` → 404.
29. Fields, skip, delete, delete-all (wrong confirm → 400) over HTTP.
30. Key: with `MATERIALS_KEY` monkeypatched, the API → 401; `/materiali`
    shows the key form; `?k=wrong` → the form with "Chiave sbagliata";
    `?k=<key>` → 303 then the API works in that client; the file GET
    needs no key.
31. Notes: start `lezione-8-social` locally, go to page 11: the admin
    slide has `notes`, `id == "S11"`, `missing == [{"id": "S11-A", ...},
    {"id": "S11-B", ...}]` and the 📦 box; `/api/live/slide` for a student
    has no `notes` key; after uploading `S11-A`, the admin slide has
    `/admin/materials/S11-A/file?v=` and the student slide
    `/api/live/material/S11-A?v=`; `/admin/api/live/notes` returns the
    same metadata.
32. Student gating: on page 11 `GET /api/live/material/S11-A` → 200 for a
    logged-in student, 401 anonymous; on page 12 → 404; with the session
    blank (paused) → 404; skipped → 404.
33. `/vero-o-falso`: the embedded JSON has 20 items and 9 available; after
    uploading I1, I1 is available with its admin URL.
34. `/vero-o-falso/carte` contains the four words; `?copie=2` repeats the
    set twice.
35. `/games/scheda-social`: logged-in student 200 with
    `commissariatodips.it`; anonymous 303 to `/`; capture host with
    `?lang=ar` 200.
36. **Manifest consistency:** every `rb-slot` id in both decks and in the
    game mocks, and every game `media.slot`, is in the manifest; every
    `deck-main` slot appears in the main deck, every `game` slot in the
    game; slot artifacts match where they are used; game slot `answer`s
    equal the items' answers; game caption placeholders equal the items'
    Italian captions.
37. **Privacy grep:** the words to avoid (the provider, the venue, the
    city, the teacher's and the assistant's names) must not be written in
    the repository, not even in a test. So the test reads them, one per
    line, from the gitignored `data/private-words.txt` at the repository
    root (`Path(__file__).parents[3] / "data" / "private-words.txt"`, not
    `DATA_DIR`; the maintainer creates it) and **skips** with a clear message when the file is
    absent (CI). Present: none of those words (case-insensitive) appears
    in any lesson 8 file: the two decks, the manifest,
    `vero_o_falso.json`, `scheda_social.json`, the new templates and the
    two new JS files. The tests write nothing there; `data/` is
    gitignored.
38. `/present` (host) contains the links `/materiali` and
    `/present/telecomando`.

### 12.2 Acceptance per package

| WP | Done when |
|---|---|
| A | tests 1-12 green; `.gitignore` committed first; `make lint` clean |
| B | page renders in the key and normal modes (F's tests 27, 30); a reading of `materiali.js` finds no `innerHTML` with data and no storage API |
| C1 | tests 13-17 green; the JSON is pretty-printed and ends with a newline |
| C2 | `/present` still passes the existing live-slide tests; CSS blocks present in both files; test 38 (after F) |
| D | tests 18-23 green |
| E | test 24 green |
| G | the four docs read as in 10; no real names |
| F | tests 25-38 green, the whole suite green, the HTTP checks of 12.3.A done |
| T | its tests green; either translations added (deck tests still green) or an explicit "Italian only" note to F |

### 12.3 Verification checklist

**A. The lead can verify here (before the roadmap commit):**

- [ ] `make lint && make test` green.
- [ ] `git status` after the tests shows nothing under `data/`.
- [ ] A throwaway server on a spare port (never the running service, no
  `.env`): `cd apps/web && SESSION_SECRET=x WEB_COOKIE_SECURE=false
  ECO_CAPTURE_HOST=mic.test DATA_DIR=$(mktemp -d) ~/.local/bin/uv run
  uvicorn rev_babel_web.main:app --port 8766`. With `curl -H "Host:
  mic.test"`: `/materiali`, `/admin/api/materials`, upload a PNG and a
  small MP4 built from bytes (`--data-binary @file`), fetch them back
  (and with `Range: bytes=0-9` → 206), `/vero-o-falso`,
  `/vero-o-falso/carte`, `/present/telecomando`; start the deck and walk
  pages 1-35 through `/admin/api/decks/lezione-8-social/slides/N` (all
  200); as a logged-in student, `/api/live/slide` and
  `/api/live/material/...` on and off the right page.
- [ ] The server log shows no file names, field contents or keys.

**B. Only a human can verify (browser, phone, classroom):**

- [ ] On the teacher's **phone**: open `/materiali` (with the key link if
  set), take a photo for I1 with the camera, pick one from the gallery
  for I3, record A1 with 🎙️, type a caption. Previews appear; nothing is
  rotated; badges and progress update; "Cosa manca" copies a list.
- [ ] On a PC: paste a screenshot with Ctrl+V into S11-A; drag a file
  onto S11-B; upload a 30-60 MB phone video (through the tunnel) for V1
  and check it plays and seeks.
- [ ] Download one uploaded phone photo back and check it has no GPS
  (any EXIF viewer).
- [ ] `/present` with `lezione-8-social`: every slide readable from the
  back; placeholders clear; S11/S25/S28 images sized well; N shows the
  notes and is hidden by default; `/present/telecomando` on the phone
  shows notes and ◀ ▶ moves the slides.
- [ ] `/follow` as a student: split screen; images appear on S11, S25,
  S28; Google Lens works on the S28 image on a classroom PC.
- [ ] `/vero-o-falso` on the projector: preload, a full category with the
  keyboard (Space, R, →, S), audio and video play, reveal chime,
  category scores, final habits, reload resumes. Arabic language line
  right-to-left (if translated).
- [ ] Print the cards (colours, one per page) and the take-home card
  (double-sided, short edge).
- [ ] Before class: each `verify` flag checked (the phone remote lists
  them) and the slides changed if needed; A1/A2 deleted after the lesson.

### 12.4 Cut line (if lesson 8 is in three days)

Protect, in order: **C1 + C2** (the decks teach on their own, with
placeholders and drawn examples) → **A + B + the F routes for
materials** (the teacher can add his photos) → **D** (the game; with no
material it still plays 9 drawn items, and the teacher can run the rest
from the slides) → E, the phone remote, T. A lesson with Italian-only
decks, placeholders on S11/S25/S28 and a game of drawn items is a better
outcome than nothing.

---

## 13. Open questions for the maintainer (from the brief, unanswered here)

1. Is there a projector in the room (the game assumes one; ADR 0014
   assumed none)?
2. Same group as the autumn course? Which languages are needed for the
   cards, the card and the captions (the cards default to en, fr, ar)?
3. Will learners have phones, or PCs only (S08 and S14's optional parts)?
4. Is the parents' deck a separate session or the second part of the day?
5. On-screen scoring or whiteboard? (Both are supported; the start screen
   chooses.)
6. Set `MATERIALS_KEY` in `.env` before using `/materiali` from the phone
   (recommended), or accept the capture-host gate alone?

