# Local `.venv` Runbook

This project should be started locally with the project virtual environment only.

## 1) Start backend

```powershell
D:\OCR\.venv\Scripts\python.exe main.py
```

## 2) Start frontend (dev)

```powershell
cd D:\OCR\frontend
npm run dev -- --host 0.0.0.0 --port 3000
```

## 3) Local sanity check

```powershell
powershell -ExecutionPolicy Bypass -File D:\OCR\scripts\selfcheck-local.ps1
```

Optional:

```powershell
powershell -ExecutionPolicy Bypass -File D:\OCR\scripts\selfcheck-local.ps1 -TaskId 123 -BatchId batch_xxx
```

## 4) Error classification used by self-check

- `backend_unready`: backend not listening or connection failure.
- `upstream_model_error`: model upstream returned `502/503/504`.
- `business_error`: expected business status like `400/404/409`.
- `server_error`: unhandled backend internal error.
