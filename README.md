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
backend/              FastAPI, SQLAlchemy, MySQL/SQLite, Alembic, tests
frontend/             Vue 3, TypeScript, Vite workbench
data/                 RAG and workflow evaluation datasets
docs/                 Project plan, user guide, and README screenshots
docs/screenshots/     Inquiry workspace and product catalog images
DEPLOYMENT.md         Docker, MySQL, Qdrant, AI provider deployment guide
PROJECT_PROGRESS.md   Implementation progress and issue-resolution log
docker-compose.yml    Local MySQL, Qdrant, backend, and frontend stack
LICENSE               MIT license
```

## Local development

### Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
DATABASE_URL=sqlite:///tradepilot.db PYTHONPATH=src alembic upgrade head
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

From the repository root, create `.env` from the example if you have not already done so, then set `MYSQL_PASSWORD` and `MYSQL_ROOT_PASSWORD` to different strong, URL-safe alphanumeric values:

```bash
[ -f .env ] || cp .env.example .env
# Edit .env and replace both placeholder MySQL passwords with unique values.
docker compose up --build
```

Do not overwrite an existing `.env` containing your local settings. Keep `.env` private; it is excluded by `.gitignore`.

The local demo frontend is available at `http://localhost:8080`; the API is available at `http://localhost:8000`. Both ports bind to localhost by default. Docker runs MySQL 8.4 on a persistent named volume and applies Alembic migrations before starting FastAPI. Docker defaults to the rules AI provider; see [DEPLOYMENT.md](DEPLOYMENT.md) for database setup, backups, and AI configuration.

## Database

Docker/production use MySQL; SQLite remains available for local development and tests. Database changes are managed with Alembic:

```bash
cd backend
export DATABASE_URL='mysql+pymysql://tradepilot:URL_SAFE_PASSWORD@127.0.0.1:3306/tradepilot?charset=utf8mb4'
.venv/bin/alembic upgrade head
.venv/bin/alembic current
```

The application also seeds deterministic demo products, inventory, and customers on startup.

### Product catalog seed data

The demo catalog is defined in `backend/src/tradepilot/seed.py` and the matching
initial stock in `backend/src/tradepilot/inventory.py`. The startup seed is
idempotent: it inserts missing SKUs only, so editing a product or adjusting its
stock in the UI is not overwritten when a container restarts. After adding a
new SKU, restart the backend with Docker Compose; the product index calibration
will synchronize the active MySQL products to Qdrant when semantic search is
enabled. Do not delete the MySQL or Qdrant volumes when applying catalog changes.

## Main API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service health |
| GET | `/api/products` | Product search |
| GET | `/api/customers` | Customer lookup |
| POST | `/api/workflow/inquiry-to-quote` | Run inquiry workflow |
| GET | `/api/quotes` | List saved quotes |
| GET | `/api/quotes/{id}` | Quote detail, risk, email draft, and approval history |
| POST | `/api/quotes/{id}/approve` | Approve a draft quote |
| POST | `/api/auth/login` | Sign in when authentication is enabled |
| POST | `/api/auth/refresh` | Rotate an access token |
| POST | `/api/auth/logout` | Revoke a refresh token |
| GET/POST | `/api/users` | Admin user management |
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

Important settings include `DATABASE_URL`, `CORS_ORIGINS`, `API_DOCS_ENABLED`, `WORKFLOW_RATE_LIMIT_PER_MINUTE`, and the optional authentication settings in `backend/.env.example`.

## AI providers

The app supports the rules engine, local Ollama, OpenAI-compatible APIs, DeepSeek, and Kimi/Moonshot. Configure `OPENAI_COMPATIBLE_*`, `DEEPSEEK_*`, or `KIMI_*` backend environment variables. Keep provider keys out of frontend configuration and Git; see [DEPLOYMENT.md](DEPLOYMENT.md) for examples.

AI configuration persistence: use the root `.env` file (or deployment-platform secrets) for `AI_PROVIDER`, provider API keys, Base URLs, model names, and timeout values. Docker Compose passes these values into the backend on every container start, so they survive backend restarts. The web AI settings panel can apply temporary runtime overrides, but those overrides are intentionally not written to MySQL or `.env`; put final values in `.env` and restart the backend before committing a deployment change.

See [DEPLOYMENT.md](DEPLOYMENT.md) for authentication, Docker, Ollama, production, and GitHub upload checks.

## Known limitations

- SQLite remains the default for direct local development; Docker Compose uses MySQL 8.4.
- Inquiry parsing supports the rules engine and optional configured model providers; product retrieval supports deterministic matching plus optional Qdrant semantic search.
- Email generation creates drafts only.
- Multi-tenant isolation, ERP/CRM integration, and real email delivery are not implemented.

## Project plan

See [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) for the full product plan and [docs/superpowers/specs/2026-09-29-foundation-design.md](docs/superpowers/specs/2026-09-29-foundation-design.md) for the first implementation specification.

For screenshots and a walkthrough of the inquiry workspace and product catalog, see the [简体中文界面使用指南](docs/USER_GUIDE.zh-CN.md).

## Interface screenshots

### Inquiry workspace

![TradePilot AI inquiry workspace](docs/screenshots/inquiry-workspace.png)

### Product catalog

![TradePilot AI product catalog](docs/screenshots/products-page.png)

## License

This project is licensed under the [MIT License](LICENSE).
