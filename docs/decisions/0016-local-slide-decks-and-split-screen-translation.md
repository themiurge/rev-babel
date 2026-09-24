# 0016. Local HTML slide decks and split-screen translation

- **Status:** accepted
- **Date:** 2026-09-24

## Context

Slide Sync Lite (ADR 0014) syncs one integer — the current slide index — from
`/present` to every connected student's `/follow` page. Until now the deck itself
was always a Google Slides file, embedded read-only in an iframe and rendered
identically for every student regardless of language.

Lesson 2's brief ("Il proprio account") is content the maintainer plans to author
directly rather than build in Google Slides, and the real payoff of doing so is
translation: since ADR 0015, every student already has a language preference. A
slide authored as data the app itself renders — not an opaque embedded document —
can show the Italian original and that student's translation side by side, which a
Google Slides embed fundamentally cannot do (translation there would mean a whole
second deck, kept in sync by hand, per language).

## Decision

**A live session now has a `source`: `"google"` (unchanged) or `"local"`.** Local
decks are JSON files under `rev_babel_web/decks/*.json` — a title and a list of
slides, each slide a dict of `{lang: html_snippet}` with `it` required. The admin
picks a deck **by title** from a dropdown on `/present` (populated from
`decks.list_decks()`) instead of pasting a URL; starting one calls
`POST /admin/api/live/start_local` with just the deck's slug, and `live.py` looks up
the title and slide count from the deck itself rather than taking them as input.
`live.py` stays deck-content-agnostic — it only tracks `deck_slug` and `index`, the
same way it only ever tracked `file_id` and `index` for Google Slides.

**The student's `/follow` page renders a real split screen for a local deck**:
Italian on the left, the student's own language on the right, fetched per-slide from
`GET /api/live/slide?index=N` — which resolves the student's language from their
session, exactly like the hover-title mechanism in ADR 0015, except this is full
visible content rather than a tooltip. If the student's language is Italian, or the
deck has no translation for their language yet, only the Italian pane shows — the
translated pane is simply absent, not blank. Each pane is boxed at a 16:9 aspect
ratio (`aspect-ratio: 16/9` in CSS) so a slide still reads like a slide even though
the space around it — sidebar, topbar, and now half the remaining width — isn't
16:9 itself. `/present` shows only the Italian pane full-width; the presenter reads
Italian regardless of who's connected.

**Translations for a local deck are content, not chrome** — shown outright, not as a
`title` hover — so they're generated the same way as ADR 0015's UI strings (one
`agy` CLI batch per language, `ITALIAN|||TRANSLATION` pairs, HTML tags preserved
verbatim and validated to still be exactly the tags that went in) but live in the
deck's own JSON rather than `i18n.STRINGS`. The two mechanisms deliberately stay
separate: UI chrome translation and slide-content translation have different
trust levels (chrome text is fixed by the app; slide content is authored per lesson)
and different display rules (hover vs. always-visible).

A three-slide sample deck (`lezione-2-account-demo.json`, all five languages) exists
now to exercise the mechanism end to end. It is not lesson 2's real content — the
maintainer will author that separately once the pipeline itself is confirmed working.

## Consequences

Easier: authoring a lesson as a local deck buys automatic, always-in-sync,
per-student translation for free — the thing Google Slides could never do here
without real duplicate decks. `live.py` needed almost no change (one more field,
one more `start_*` function); the SSE/index-sync core is untouched and still
doesn't know or care what a "slide" actually contains.

Harder: two separate ways to build a lesson now exist (paste a Google Slides link,
or author a JSON deck) with different authoring workflows and no conversion between
them. `/admin/api/decks/{slug}/slides/{index}` (the presenter's preview endpoint)
and `/api/live/slide` (the student's) are both gated only the same way their
surrounding pages already are — capture-host-only and logged-in-student-only,
respectively — so this doesn't add new attack surface, but it does add two more
endpoints to that same accepted-risk list from issue 0001. As with ADR 0015's
strings, deck translations are machine-generated and unreviewed — same caveat,
now covering slide content that students read directly rather than just hover
over.
