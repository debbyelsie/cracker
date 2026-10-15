# Cracker — Research Studio

A local first version of Cracker: a Next.js interface connected to a small FastAPI service. The service returns clearly labelled fictional demonstration findings; it does not search the web or provide real research evidence.

## Requirements

- Node.js 20.9 or newer and npm
- Python 3.10 or newer

## Run on Windows (PowerShell)

Open two PowerShell terminals in this folder.

### 1. Start the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0
```

The API runs at `http://localhost:8000`; its health check is `http://localhost:8000/api/health`.

### 2. Start the frontend

In the second terminal, from the project folder:

```powershell
npm install
npm run dev -- --hostname 0.0.0.0
```

Open the `Local` URL printed by Next.js (usually `http://localhost:3000`). If you are opening the app from a browser that cannot reach `localhost`, use the `Network` URL printed by Next.js instead. Enter a question of at least 12 characters and optionally add context. Choose a finding to inspect its fictional sample evidence.

If PowerShell blocks virtual-environment activation, use `backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt` and `backend\.venv\Scripts\python.exe -m uvicorn app.main:app --reload` from the project root instead.

## Tests

With the backend virtual environment activated from the `backend` folder:

```powershell
python -m pytest
```

The tests cover the health endpoint, structured demo response, and question validation.

## Project map

- `src/app/page.tsx` — interactive Research Studio and evidence inspection.
- `src/app/globals.css` — responsive visual system and Cracker palette.
- `backend/app/main.py` — FastAPI endpoints and CORS.
- `backend/app/schemas.py` — request and response validation models.
- `backend/app/research.py` — isolated simulated research workflow.
- `backend/tests/test_research.py` — API behavior tests.
