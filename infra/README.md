# infra

Deployment configuration for running rev-babel's services together on the
teacher's desktop. See `docs/architecture.md` for the topology this
configures and `docs/operations.md` for the runbook.

## What belongs here

`compose.yaml` and anything needed to bring the stack up as a unit;
`tunnel/` for Cloudflare Tunnel configuration.

## What does not belong here

Application or service code — those live in `apps/` and `services/`.

## Status

Placeholder. `compose.yaml` defines no runnable services yet.
