# 0007. Choose the translation model

- **Status:** open
- **Owner:** 💻 code
- **Milestone:** M1
- **Opened:** 2026-09-05

## Context

Two candidate classes: a small dedicated MT model (fast, tiny, weakest on
Arabic and on code-switched input) and an instruction-tuned LLM used solely
for translation (handles mixed Italian/English natively, costs more VRAM).
[ADR 0006](../decisions/0006-dedicated-translation-model.md) separates
translation from *Play's* chat model, not from all chat models.

## What it takes

Run both against the corpus and FLORES, record chrF++, latency and VRAM,
and decide. The smaller model stays as the degradation path either way.

## Done when

A decision record quoting the measured numbers, and `MT_BACKEND` set accordingly.
