# File Structure Plan

## Backend target tree

```text
app/
  interfaces/
    api/
      v1/
        router_registry.py
  application/
    workflows/
      tasks.py
      batches.py
      archives.py
      qa.py
      evaluation.py
  domains/
    ingestion/
    extraction/
    archive/
    batch_ai/
    qa_eval/
    auth/
  infrastructure/
    persistence/
    cache/
    queue/
    storage/
    ocr_runtime/
    llm_clients/
  shared/
    contracts.py
```

## Frontend target tree

```text
frontend/src/
  features/
    workbench/
    result/
    batch-insights/
    search/
    auth/
  entities/
  shared/
    api/
    ui/
    copy/
```

## Migration rules

- Add new layers first, then migrate implementations.
- New features must enter `features` / `application` / `domains`, not legacy giant files.
- Keep each migration step buildable and reversible.
- Preserve API compatibility first, then retire legacy adapters.
