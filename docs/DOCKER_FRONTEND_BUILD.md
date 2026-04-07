# Frontend Docker Build Baseline

## Local vs Docker output strategy

- Local FastAPI static hosting: Vite default output is `../static/vue`.
- Frontend Docker image build: force `VITE_OUTPUT_DIR=dist` and copy from `/app/dist`.

## Required command (root context)

```bash
docker build -f frontend/Dockerfile .
```

Do not run `docker build -f frontend/Dockerfile frontend` for this repository layout.

## Current `frontend/Dockerfile` assumptions

- package manager: `npm` (`npm ci`).
- build output inside image: `/app/dist`.
- runtime image: `nginx:alpine`.
