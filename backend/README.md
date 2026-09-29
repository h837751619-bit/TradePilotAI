# TradePilot Backend

## Setup

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Test and lint

```bash
PYTHONPATH=src pytest
ruff check src tests
```

## Run locally

```bash
PYTHONPATH=src uvicorn tradepilot.main:app --reload
```

The API seeds local demo products into `tradepilot.db` on startup.

## Evaluation

Run the deterministic evaluation set from the backend directory:

```bash
PYTHONPATH=src .venv/bin/python scripts/evaluate.py
```

## Docker

From the project root:

```bash
docker compose up --build
```

The frontend is available at `http://localhost:8080` and the API at `http://localhost:8000`.

The first Product RAG layer is available as a deterministic retrieval helper in
`tradepilot.rag.products`. It formats product records into knowledge documents
and ranks keyword matches without requiring an external embedding service.

Endpoints:

- `GET /health`
- `GET /api/products?q=hotel`
- `GET /api/products?category=Outdoor%20Chair&limit=10`
