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
