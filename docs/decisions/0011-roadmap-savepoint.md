# 0011. A roadmap savepoint at the root, and issues as files

- **Status:** accepted
- **Date:** 2026-09-05

## Context

The project had documentation of two kinds — how the system is designed
(`docs/`) and how it gets built (`plans/`) — and no record of where it
actually *is*. Status lived in commit messages and in whatever the last
working session happened to remember. With one maintainer, long gaps
between sessions, and a fixed external deadline, that is the thing most
likely to be lost.

A GitHub issue tracker would hold the backlog, but it would put the work
items somewhere the rest of the project is not: unreadable offline,
absent from a clone, and versioned separately from the decisions and plans
they relate to. For a single-maintainer repository, a tracker nobody else
reads is a second place to look rather than a place to look.

The convention adopted here is taken from a sibling project of the
maintainer's, adapted rather than copied.

## Decision

`ROADMAP.md` at the repository root is the durable savepoint: what is true
now, what is in flight, what is next, and a revision log. Certainty tapers
outward — the near term is concrete, the horizon deliberately rough.

Issues are markdown files in [`issues/`](../issues/README.md), numbered
sequentially and never renumbered, following the same rule as these
decision records. Each carries a status, an owner, and a condition that
says when it is done.

Owners are one of two kinds: **🧑 Emilio**, for anything needing a human —
an account, a purchase, a room, a judgement — and **💻 code**, for anything
a working session can do against this repository. The distinction exists
because the human items have lead times and the code items do not.

The roadmap is a whiteboard, not a contract: it reflects decisions, it does
not make them. Anything load-bearing is decided in an ADR first. Every
working session closes by refreshing "Where we are now" and adding a
revision log entry.

Deliberately not adopted from the source convention: autonomous
implementing agents, bot identities, and merge-gate machinery. This project
has one maintainer working directly on `main`, and that machinery would be
overhead with nothing to hold.

## Consequences

Easier: a session can be resumed from a cold start by reading one file and
following its links; status, backlog, decisions and plans are one clone and
one history; the honest distinction between "configured" and "confirmed
working" has somewhere to live, which matters for a system whose failure
mode is discovering something at 16:30 on a Thursday.

Harder: the roadmap only stays true if it is updated, and nothing enforces
that but the session-end ritual. `docs/roadmap.md` — a build sequence that
predates this record — is superseded by the savepoint's Horizon section and
removed, so there is one place where sequencing lives rather than two that
can disagree.
