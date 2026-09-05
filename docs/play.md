# Play

The roleplay practice module. As designed; nothing below is implemented
yet — see `services/llm/README.md` for current (placeholder) status.

## What it does

Students practise real-life situations — asking for directions, a doctor's
appointment, a shop transaction — in spoken conversation with a language
model playing the other role.

## Why input is spoken, not typed

Typing is itself a barrier for this group, separate from the language being
practised (see `overview.md`). Play is designed around speaking and
listening, matching the skill the course and the students' daily lives
actually require, and not adding a keyboard-fluency requirement on top.

## Why conversation history is not shown

The interface deliberately does not display a transcript of the ongoing
conversation. TODO: the specific interaction design (turn-taking cues, how
a student ends a session) is not yet decided.

## Privacy note

Play sessions are spoken conversation, potentially about personal
situations. See `data-and-privacy.md` — these are not displayed to anyone
but the student having the conversation, and are not stored as a readable
transcript.

## Unbuilt

`services/llm` is a placeholder at this stage. Model choice, quantisation,
and hosting details are open — see `open-questions.md`.
