# Data and privacy

This is the most important document in this repository. Read it before
adding any file, fixture, example, or test data.

## Who the users are

Adult migrant women attending a computer-literacy course, several with
young children who may be present in the classroom or nearby. This
repository is public. These two facts together are why the rules below are
not negotiable — see `overview.md` for the full teaching context.

## What is stored, where, for how long

- **Avatars** — the picker uses a preset collection of ready-made
  avatars, claimed by each user on first use (see
  [ADR 0010](decisions/0010-avatar-picker.md), which supersedes
  [ADR 0007](decisions/0007-no-login-picker.md)). They depict nobody real,
  so the art itself is not personal data and lives in the repository like
  any other static asset. What is stored per user is a user id, the
  avatar claimed against it, and a language preference — no name, and no
  photograph of anyone.
- **Eco transcripts** — TODO: retention period not yet decided. Whatever is
  decided, transcripts are of the teacher's speech only (see below), and
  none belong in this repository as sample or fixture data.
- **Play sessions** — personal, potentially about a student's real
  situation. Play conversations are not displayed as a readable transcript
  in the interface, to any user including the student who had them. TODO:
  whether anything is retained server-side, and for how long, is not yet
  decided.
- **Attendance and progress** — visible to the teacher only. Never shown to
  other students, never to the teaching assistant beyond what live support
  requires.
- **Only the teacher's voice is transcribed.** Student and teaching
  assistant audio captured incidentally by the same pipeline is discarded,
  not transcribed and not stored.

## What is deliberately not stored

- No recordings of any kind, of anyone, beyond what a fallback mechanism
  requires transiently (if any — TODO, see `operations.md`).
- No photograph anywhere in version control. Since
  [ADR 0010](decisions/0010-avatar-picker.md) the system holds no
  photograph of any user at all, on the server or off it — this rule now
  describes the design rather than restraining it.
- No transcript, real or sample, in this repository.

## Repository rules (binding on every future contributor)

- **No student names.** Not in docs, fixtures, examples, or comments. Use
  role labels (`student_a`, `assistant`) or clearly fictional names.
- **No photographs** committed anywhere in the repository's history.
- **No transcripts or recordings**, real or sample, anywhere in the
  repository.
- **No `.env`** — only `.env.example`, and in it every secret is left
  empty: tunnel credentials, cookie signing keys, bearer tokens, API
  keys. Non-secret configuration — hostnames, ports, paths, model names —
  may carry its real value there, since there is nothing to protect and a
  wrong one costs a lesson.
- **Nothing identifying the course provider, venue, or address.**
- `.gitignore` blocks `data/`, `.env`, `*.wav`, `*.mp3`, `*.ogg`, `*.webm`,
  `models/`, and `*.db`. If a change needs a new category of local or
  runtime data, extend `.gitignore` before adding the file that needs it —
  do not commit first and clean up after.

If you are about to add an example, fixture, or test value and reach for a
name, a face, or a real sentence a student might have said — stop. Use a
role label and an invented, clearly fictional example instead.
