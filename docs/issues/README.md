# Issues

The atomic backlog. One file per issue, numbered sequentially and never
renumbered or reused — the same rule as
[`decisions/`](../decisions/README.md).

There is no issue tracker: this repository has one maintainer, and a
tracker nobody else reads is a second place to look. Issues live here so
that the roadmap, the decisions and the work items are all in one clone,
readable offline and versioned by the same git history.

[`../../ROADMAP.md`](../../ROADMAP.md) is the savepoint that points at
these; it holds priority and direction, and these hold detail. An issue is
"in flight" because the roadmap's **Now** section says so, not because of
anything written here.

## Format

```
# NNNN. Title

- **Status:** open | blocked | done | dropped
- **Owner:** 🧑 Emilio | 💻 code
- **Milestone:** M1–M6, or — for anything outside the milestone plan
- **Opened:** YYYY-MM-DD
- **Closed:** YYYY-MM-DD   (only once it is)

## Context
What situation makes this worth doing, and what breaks if it is not.

## What it takes
The shape of the work. Not a specification — the plan files carry that.

## Done when
A condition someone else could check.
```

## Owners

- **🧑 Emilio** — needs a human: an account, a purchase, a room, a phone,
  a judgement call, or a decision only the maintainer can make.
- **💻 code** — can be done in a working session against this repository.

The split matters because the 🧑 items have lead times and the 💻 items do
not. An issue blocked on a 🧑 item should say so.

## Status

- **open** — actionable now.
- **blocked** — waiting on something named in the issue. Several are
  blocked until lesson 1 (17 September 2026), which is *after* the system
  has to work; where that is true, a companion issue exists to make either
  answer survivable.
- **done** — keep the file, set the date, say what actually happened if it
  differed from the plan.
- **dropped** — keep the file, say why. A dropped issue is a decision.

## Closing one

Set the status and the closing date, add a line saying what happened, and
update the roadmap's **Where we are now** in the same commit. If closing it
settled something load-bearing, the decision belongs in
[`decisions/`](../decisions/README.md) — the issue records that the work
happened, not what was decided.
