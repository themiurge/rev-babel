# 0015. Permanent named accounts, a language preference, and hover translation

- **Status:** accepted
- **Date:** 2026-09-24

## Context

Lesson 1 happened. ADR 0013's typed-name screen worked, but it created a new,
disconnected student row on every single visit — so a returning student lost her
whole score history the moment her session cookie expired or she opened a new
browser tab. That was fine for a one-off dress rehearsal; it stops being fine once
three named students (Benita, Harzhin, Mousrietou) are expected to keep using this
across ten weekly lessons.

Lesson 1 also answered part of issue 0020 (the students' first languages): not with
certainty about native tongues, but with a concrete "second language" each student
wants support in - English, Kurdish, and French respectively. The maintainer named
the Kurdish one only as "the northern Iraq variant" without knowing its formal
name. Issue 0008 already anticipated this exact ambiguity and settled on `ckb`
(Sorani / Central Kurdish, ISO 639-3) as the code to evaluate - the Kurdistan
Region of Iraq's dominant written variant, as opposed to `kmr` (Kurmanji), which is
more associated with Turkey and Syria. This ADR adopts `ckb` on that basis. It is
still a guess, not a confirmed fact about any student's dialect, and should be
corrected the moment someone who'd know says otherwise.

## Decision

**Accounts are permanent, not per-session.** A student row, once created, is
looked up by name (case-insensitive) rather than recreated. The login page
(`/`) shows every existing student as a one-tap button; typing a name below it
only creates a new row if no case-insensitive match exists. `POST /login/{id}`
logs in as an existing student directly.

**Each student has a `language` column** - one of `it` (no second language;
the default) or the four now supported: `en`, `fr`, `ckb`, `ar`. A brand new
account's language defaults to whatever the always-visible dropdown was last
set to in that browser (tracked via a plain `rev_babel_lang` cookie before any
account exists), matching what the student just picked to read the login page
itself.

**Every Italian UI label optionally carries an HTML `title` attribute** holding
its translation in the student's current language - a native browser tooltip,
not a replacement of the Italian text, and not shown at all when the language
is `it`. Translations are looked up by the Italian source text itself
(`i18n.STRINGS[text][lang]`), so there is no separate key scheme to keep in
sync with the templates. The dropdown (top right on every page, plus the login
page) changes the preference with one request to `POST /api/language` and a
full page reload - deliberately not a live client-side re-render, to keep the
mechanism to "server renders the right `title` attributes," nothing more.

The four languages' initial translations were machine-generated in one batch
per language via the `agy` CLI in headless mode (`agy -p "translate..."`),
each given the full list of Italian source strings and asked to return
`ITALIAN ||| TRANSLATION` pairs only. They have **not been reviewed by a
native speaker of any of the four languages** and should be treated as a
first pass.

## Consequences

Easier: a student's history, name, and language preference now survive
indefinitely across logins, browsers, and lesson weeks - the actual
requirement, once there is a real roster rather than a dress rehearsal.
Recognizing your own name in a row of buttons needs no typing at all, which
partially restores the "recognition over reading" principle ADR 0007 and
ADR 0010 were built around, even though the underlying mechanism is still a
typed name (ADR 0013's stopgap is unchanged, not superseded).

Harder: this is now genuinely permanent personal data (a name, tied to a
persistent id, tied to a language and game-score history) living in
`data/rev_babel.db` - not committed, per `docs/data-and-privacy.md`, but no
longer a same-session throwaway either. The dedup-by-name lookup is
case-insensitive only; two different real students who happen to share a
name would collide into one account, silently. Nobody reviewed the machine
translations, so a wrong or awkward phrase could reach a student before a
human catches it - most likely for Kurdish, both because it's the
least-resourced of the four languages for machine translation and because
even the variant choice is unconfirmed.

## Open follow-ups

- Confirm with someone who'd know whether Harzhin's Kurdish is really Sorani
  (`ckb`) rather than Kurmanji (`kmr`) - this closes issue 0008's remaining
  half.
- Have a native or fluent speaker spot-check the `en`/`fr`/`ckb`/`ar` strings
  in `apps/web/src/rev_babel_web/strings.json` before relying on them for
  something more consequential than a button hover.
- Decide what happens when two students share a name (issue TBD - not filed
  yet, since it hasn't happened).
