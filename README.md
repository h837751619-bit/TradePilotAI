# TradePilot AI

AI Export Sales Agent for B2B Cross-Border Trade.

TradePilot turns an English B2B export inquiry into a structured sales workflow:

```text
Inquiry → Requirement Parsing → Customer Lookup → Product Search
→ Inventory Check → Pricing → Quote Draft → Risk Check
→ Human Approval → Email Draft → Agent Trace
```

## Current status

This repository contains a portfolio-ready MVP using simulated Nova Outdoor data. It is designed for local development and Docker demonstration. It does not send real emails, connect to a production ERP, or make autonomous commercial commitments.

## Repository structure

```text
backend/        FastAPI, SQLAlchemy, SQLite, Alembic, tests
frontend/       Vue 3, TypeScript, Vite workbench
data/           Evaluation datasets
docs/           Project plan and engineering specifications
docker-compose.yml
```

## Local development

### Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
PYTHONPATH=src alembic upgrade head
PYTHONPATH=src uvicorn tradepilot.main:app --reload
```

The API runs at `http://localhost:8000`. Swagger is available at `/docs` in development.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The workbench runs at `http://localhost:5173` and proxies API requests to the backend.

## Docker

From the repository root:

```bash
docker compose up --build
```

The production-style frontend is available at `http://localhost:8080`; the API is available at `http://localhost:8000`. The backend container runs `alembic upgrade head` before starting FastAPI and persists SQLite data in a Docker volume.

## Database

The MVP intentionally uses SQLite. Database changes are managed with Alembic:

```bash
cd backend
DATABASE_URL=sqlite:///tradepilot.db .venv/bin/alembic upgrade head
.venv/bin/alembic current
```

The application also seeds deterministic demo products, inventory, and customers on startup.

## Main API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service health |
| GET | `/api/products` | Product search |
| GET | `/api/customers` | Customer lookup |
| POST | `/api/workflow/inquiry-to-quote` | Run inquiry workflow |
| GET | `/api/quotes` | List saved quotes |
| POST | `/api/quotes/{id}/approve` | Approve a draft quote |
| GET | `/api/agent-runs` | Read workflow traces |
| GET | `/api/evaluation` | Read evaluation metrics |

## Evaluation

```bash
cd backend
PYTHONPATH=src .venv/bin/python scripts/evaluate.py
```

The deterministic dataset covers successful inquiries plus missing quantity, unknown product, and insufficient inventory cases.

## Verification

```bash
cd backend
PYTHONPATH=src .venv/bin/pytest
.venv/bin/ruff check src tests scripts

cd ../frontend
npm run build
```

## Configuration

Copy the examples before local customization:

```bash
cp backend/.env.example backend/.env
cp .env.example .env
```

Important settings include `DATABASE_URL`, `CORS_ORIGINS`, `API_DOCS_ENABLED`, and `WORKFLOW_RATE_LIMIT_PER_MINUTE`.

## Known limitations

- SQLite is used instead of MySQL for the MVP.
- Inquiry parsing and product retrieval are deterministic; an LLM and vector database are not yet connected.
- Email generation creates drafts only.
- Authentication, authorization, multi-tenancy, ERP/CRM integration, and real email delivery are not implemented.

## Project plan

See [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) for the full product plan and [docs/superpowers/specs/2026-09-29-foundation-design.md](docs/superpowers/specs/2026-09-29-foundation-design.md) for the first implementation specification.
