# 0018. Lesson 6's tutor chatbot: Anthropic, Sonnet, nothing stored

- **Status:** accepted
- **Date:** 2026-11-02

## Context

Lesson 6 is about artificial intelligence. The maintainer wants a chatbot that
teaches the class how to use chatbots by being one: short guided missions
(ask a clear question, give context, ask for a simpler answer, use your own
language, check the answer, don't share personal data), not a blank box.

Nothing in the repository runs a language model yet. `services/llm` is
reserved for Play's spoken roleplay on the local GPU, and its model size is
still an open question ([`open-questions.md`](../open-questions.md)). Lesson 6
cannot wait for that, and a teaching chatbot has to be good at simple
Italian and at five support languages, two of them low-resource (`ckb`,
`kmr`). So the question was which hosted provider, and what that means for
the students' text.

Until now, nothing a student wrote left the teacher's machine. The class chat
([ADR 0017](0017-class-chat.md)) keeps messages in memory for a day; the
lesson 5 editors send nothing at all. A tutor chatbot necessarily sends what
the student types to a third party.

## Decision

**Provider and model (the maintainer's decision).** The tutor calls the
Anthropic Messages API through the official `anthropic` Python SDK, with one
model, `claude-sonnet-5-5`. The model ID is a single constant in
`rev_babel_web/tutor.py`, overridable with `TUTOR_MODEL` in `.env`. The key
is `ANTHROPIC_API_KEY`, read from `.env` only, passed to the client
explicitly (so the SDK never picks up some other credential on the machine),
and never logged. `.env.example` carries it empty.

**It lives in `apps/web`, not `services/llm`.** It is a thin client for a
hosted API, not model inference; `services/llm` stays reserved for Play's
local model. `rev_babel_web/tutor.py` holds the client, the prompt, the
limits and the scripted fallback.

**The page.** `/games/tutor`, opened in a new tab from the lesson 6 page like
the lesson 4 and 5 tutorials, so it gets the whole screen: missions on the
left, the chat on the right, one column on a phone. Seven missions plus a
closing page of five rules. Each mission shows a bad and a good example
prompt and why the good one works, and offers tappable example prompts that
fill the input box (the student still presses Invia). Every label, example and
scripted answer is in Italian with the student's language under it, RTL for
`ckb` and `ar`. A "Rispondi in" toggle (Italiano / her language / both) tells
the tutor which language to answer in; "both" puts the Italian first and the
translation under it, like the split-screen decks of
[ADR 0016](0016-local-slide-decks-and-split-screen-translation.md). Mission 5
is about languages: translating, asking for an answer in her language, and
checking a translation by translating it back.

**The persona.** A static system prompt (prompt-cached) makes the tutor say it
is a program and never a person, answer briefly in simple Italian, never
invent numbers, addresses, hours or rules, refuse to repeat personal data,
and end every reply with one "💡" line about how the student asked. A second,
small system block names the current mission and the reply language.

**What leaves the machine, and what is kept.** Only the current message and
the last six turns of the current mission go to Anthropic. Nothing is stored
by the app: not on disk, not in the database, not in a log line (a failed call
logs the exception's class name only). The conversation lives in the
browser tab's memory, sent back with each message; it is cleared when the
student changes mission, presses "Cancella la chat", or closes the tab. The
server keeps only per-student request timestamps for the rate limit, in
process memory (one uvicorn worker, as for ADRs 0014 and 0017).

**The transcript stance, adapted from Play.** [`play.md`](../play.md) says
Play conversations are never shown as a readable transcript, to anyone. A
typed chat cannot teach without showing the student the reply she is reading,
so the tutor shows the current exchange on her own screen only, and nothing
more: no history page, no teacher view, no export, nothing kept after the
mission or the tab. Nobody else can read it.

**Personal data is stopped before it is sent.** Messages that look like a
password, an email address, a codice fiscale, an IBAN, a run of nine or more
digits (phone, card, document) or an ID-card number are refused, in the
browser and again on the server, and never reach Anthropic. The student sees
a bilingual "Fermati!" warning, which is itself mission 7's lesson. Earlier
turns are re-checked the same way. The filter is deliberately broad; a false
positive costs one rephrased question.

**Cost bounds.** 400 characters per message, six turns of history (each
capped at 1,500 characters), `max_tokens` 800, `effort: low`, a 20-second
timeout with one retry. Per student, 6 calls a minute and 80 a day; for the
whole class, `TUTOR_DAILY_LIMIT` (default 400) per rolling 24 hours. Over a
limit the student gets "aspetta un minuto" and nothing is sent. On this
model, the server-side refusal fallback (`fallbacks: "default"`) is on.

**Degrading.** With no key, the page says the tutor is offline and answers
from scripted, bilingual content: each example prompt has an example answer,
and free text gets the mission's tip. When a call fails or is refused, the
same scripted answer is shown with "il tutor non risponde adesso". The lesson
works with no internet beyond the app itself.

## Consequences

Students' free text now goes to a third party, Anthropic, under the
maintainer's API account and Anthropic's API data-retention terms, which this
repository does not control. That is the privacy cost of this decision. It is
mitigated, not removed, by the filter, the short history window, the
on-screen warnings (the privacy line above the chat, the "your sentences go to
a company's computer" note, and mission 7), and by keeping nothing locally.
A student can still type something personal that the filter does not
recognise (a street name, a diagnosis in words); the tutor is instructed not
to repeat it, but it has been sent.

Easier: lesson 6 works now, in all six languages, without a local model, and
without a key it still works as a scripted lesson. Harder: a recurring,
usage-based cost on the maintainer's account (bounded by the limits above),
and one more external dependency (`anthropic`) in `apps/web`. The tutor
needs the internet; the classroom network (issue 0002) matters for it.

Not verified at the time of writing: the tutor against the real API (no key
was configured), and the page in a real browser on the classroom machines or
a phone. The machine-written translations of the tutor's content (en, fr,
ckb, kmr, ar) are unreviewed, like those of ADR 0015.
