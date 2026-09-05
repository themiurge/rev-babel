# 0001. Protect the capture host

- **Status:** open
- **Owner:** 🧑 Emilio
- **Milestone:** M4
- **Opened:** 2026-09-05

## Context

Found live on 5 September: `mic.emiliovicari.com` serves its page with no
challenge — the request reaches the origin directly. Today that is a test
page. Once the capture endpoint exists, that URL opens a microphone in a
room with five students and their children.

## What it takes

Cloudflare Access on the capture host only (one-time PIN, free at one
seat), and/or `CAPTURE_TOKEN` rotated per lesson. The caption host stays
open: a student cannot be asked to read an email and type a code
([ADR 0010](../decisions/0010-avatar-picker.md)).

## Done when

An unauthenticated request to the capture host is refused, and the caption host still loads with nothing to type.
