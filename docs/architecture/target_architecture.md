# Target Architecture (Modular Monolith)

This document defines the refactored target architecture for the HR archive system.

Diagram file (standalone deliverable):
- `docs/architecture/target_architecture.mmd`

## 1. Goals

- Keep single-process deployment for simple operations.
- Separate transport logic from business orchestration and domain rules.
- Preserve current `/api/ocr/*` compatibility.
- Enable future AI capabilities without another large rewrite.

## 2. Layer Responsibilities

- `interfaces/api/v1`
  - Auth guard, request validation, error mapping, DTO serialization.
  - No direct OCR/LLM SDK calls.
- `application/workflows`
  - Cross-domain orchestration: upload, task queueing, batch analysis, QA, evaluation.
- `domains`
  - Business rules by bounded context:
  - ingestion, ocr, extraction, archive, batch_ai, qa_eval, auth.
- `infrastructure`
  - DB/cache/queue/storage/runtime client implementations.
- `shared`
  - Cross-layer contracts and shared primitives.

## 3. Compatibility Strategy

- Keep external API paths stable.
- Keep `app/api/routes.py` as a compatibility shell during migration.
- Route all new logic through `application + domains`.

## 4. Migration Track

- Phase A: structure and router registration baseline.
- Phase B: migrate core flows (tasks, batches, QA, evaluation, archives).
- Phase C: standardize OCR/LLM provider abstractions.
- Phase D: remove duplicated legacy paths after regression confidence.
