# 0008. Check coverage for Sorani and Kurmanji

- **Status:** open
- **Owner:** 💻 code
- **Milestone:** M1
- **Opened:** 2026-09-05

## Context

A student's first language may be Sorani or Kurmanji Kurdish, and that is
established *in lesson 1* — two days after the system must work (see issue
0020). Discovering live that neither is servable would be avoidable.

## What it takes

Run the same evaluation for `ckb` and `kmr` alongside en/fr/ar. Keep the
target set configuration rather than code.

## Done when

A recorded quality figure for both, so either answer in lesson 1 is survivable.

## Update — 2026-09-24

Lesson 1 happened; Harzhin's support language is Kurdish, "the northern Iraq
variant," per the maintainer, who didn't know its name. `ckb` (Sorani) was
adopted for the hover-translation UI strings (ADR 0015) on the reasoning
above — the Kurdistan Region of Iraq's dominant written variant — but this
is still the maintainer's guess, not a confirmed fact. This issue stays
open until someone who'd know confirms `ckb` over `kmr`, and until the
actual MT-quality evaluation this issue asks for has been run for Eco.
