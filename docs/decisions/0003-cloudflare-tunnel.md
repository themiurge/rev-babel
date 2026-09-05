# 0003. Cloudflare Tunnel for public access

- **Status:** accepted
- **Date:** 2026-09-05

## Context

The system is reached from the classroom over the internet, from a home
connection likely behind CGNAT with a dynamic IP. Browsers also require
HTTPS for microphone access, which the phone-as-microphone design
([ADR 0004](0004-phone-as-microphone.md)) depends on.

## Decision

Expose the server via a Cloudflare Tunnel. No ports are forwarded on the
home router.

## Consequences

Easier: works behind CGNAT and a dynamic IP without router configuration;
supplies HTTPS, which the browser microphone API requires. Harder: adds a
dependency on Cloudflare's tunnel service being up, which is itself a
failure mode recorded in `docs/operations.md`.
