# 0016. Draw the avatars

- **Status:** open
- **Owner:** 🧑 Emilio
- **Milestone:** M5
- **Opened:** 2026-09-05

## Context

[ADR 0010](../decisions/0010-avatar-picker.md) replaced login photographs
with a preset collection. Twelve to sixteen for six users, so choosing is a
real choice. Produced outside this repository; not on the critical path for
lesson 1.

## What it takes

Distinguishable at tile size by silhouette and background colour, not
facial detail — the users cannot be assumed to read the labels that would
otherwise tell them apart. Free of anything that reads as ethnic or
religious caricature.

## Done when

A manifest (`id`, file, background colour) plus assets, reviewed at actual tile size on a classroom machine.
