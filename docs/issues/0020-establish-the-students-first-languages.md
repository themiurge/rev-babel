# 0020. Establish the students' first languages

- **Status:** open (partially answered)
- **Owner:** 🧑 Emilio
- **Milestone:** —
- **Opened:** 2026-09-05

## Context

Likely Arabic, possibly Sorani or Kurmanji Kurdish. Blocked until lesson
1 (17 September 2026) — which is after Eco must work. Issue 0008 exists so
that either answer is survivable.

## What it takes

Ask, in lesson 1. Then replace the entry in
[`open-questions.md`](../open-questions.md) with a decision.

## Done when

The target language set is known and configured.

## Update — 2026-09-24

Lesson 1 happened and gave a *second*-language answer, not necessarily a
confirmed first-language one: Benita → English, Harzhin → Kurdish (assumed
Sorani, `ckb` — see issue 0008), Mousrietou → French. Recorded and wired
up as ADR 0015. Configured in `apps/web/src/rev_babel_web/i18n.py` and the
three students' `language` column.

Left open: whether these are genuinely first languages or just the
support language each student asked for is not distinguished here, and
the Kurdish variant is still the maintainer's best guess, not confirmed —
issue 0008 remains open on that point.
