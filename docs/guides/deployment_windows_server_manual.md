# Windows Server Manual Deployment (Non-Docker)

This guide preserves the same repository structure used by Docker while running services directly on Windows Server.

## 1) Prerequisites

- Windows Server 2019/2022
- Python 3.11+
- Node.js 20+
- PostgreSQL 16+
- Git

## 2) Clone and Configure

```powershell
git clone <repo-url> C:\openli\dmm
cd C:\openli\dmm
copy .env.example .env
```

Set in `.env` (minimum):

- `DM_DATA_ROOT=C:\openli\dmm`
- `DM_API_HOST=0.0.0.0`
- `DM_API_PORT=9134`
- `DMM_TOKEN_SECRET=<strong-secret>`
- `DM_DATABASE_URL=postgresql://dmm_app:<password>@127.0.0.1:5432/dmm`
- `NEXT_PUBLIC_DM_API_BASE=http://127.0.0.1:9134`
- `DM_ALLOW_ORIGINS=http://localhost:9133,http://127.0.0.1:9133,http://localhost:9135`

## 3) Backend (FastAPI)

```powershell
cd C:\openli\dmm\services\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DM_DATA_ROOT="C:\openli\dmm"
$env:DM_API_HOST="0.0.0.0"
$env:DM_API_PORT="9134"
uvicorn app.main:app --host 0.0.0.0 --port 9134
```

## 4) Frontend (Next.js)

```powershell
cd C:\openli\dmm\services\frontend
npm install
$env:NEXT_PUBLIC_DM_API_BASE="http://127.0.0.1:9134"
npm run build
npm run start -- -p 9133
```

## 5) Reverse Proxy (Optional but Recommended)

Use IIS/ARR or Nginx for Windows to expose a single entrypoint on `9135`:

- `/api/*` -> `http://127.0.0.1:9134`
- all other paths -> `http://127.0.0.1:9133`

## 6) Service Persistence

Use Windows Services (NSSM/SC) for:

- FastAPI backend on `9134`
- Next.js frontend on `9133`
- Optional reverse proxy on `9135`

## 7) Port Policy

Keep host ports in `9133-9139` for parity with Docker:

- `9133` frontend
- `9134` backend
- `9135` ingress/proxy
- `9136` postgres (if exposed)

## 8) Feasibility Note

Yes, full local deployment without Docker is possible while keeping the same project structure. The key is to keep `DM_DATA_ROOT` pointing to repo root so pipeline, schemas, mock data, and reports resolve identically in both modes.
