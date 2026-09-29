# TradePilot AI Foundation Implementation Plan

## Goal

完成第一阶段基础：FastAPI 服务、SQLAlchemy + SQLite 产品数据、可复用产品查询服务、模拟产品种子数据和自动化测试。

## Constraints

- Python 3.12+
- 第一阶段不接 LLM、RAG、Redis、MCP 或外部服务
- 测试使用临时 SQLite 数据库
- 不提交数据库文件、密钥或本机环境配置
- 遵循 RED → GREEN → REFACTOR

## Task 1: Backend project setup

### Files

- `backend/pyproject.toml`
- `backend/src/tradepilot/__init__.py`
- `backend/tests/__init__.py`

### Steps

1. Write a test that imports the package and verifies the project exposes the expected package metadata.
2. Run the focused test and confirm it fails because the package is not implemented.
3. Add the minimal package structure and dependencies: FastAPI, Uvicorn, SQLAlchemy, Pydantic settings support, pytest, and Ruff.
4. Run the focused test and then the backend test suite.

### Expected

The backend can be installed in editable mode and pytest discovers tests.

## Task 2: Database and Product model

### Files

- `backend/src/tradepilot/db.py`
- `backend/src/tradepilot/models.py`
- `backend/tests/test_models.py`

### Steps

1. Write tests for creating the products table, inserting a Product, enforcing the unique SKU, and reading the product fields.
2. Run the tests and confirm the expected failure.
3. Implement the SQLAlchemy engine/session factory and Product model.
4. Keep database initialization explicit through a `create_tables` function.
5. Run the model tests and the full suite.

### Expected

A temporary SQLite database can create and persist Product records without depending on a local database file.

## Task 3: Deterministic seed data

### Files

- `backend/src/tradepilot/seed.py`
- `backend/tests/test_seed.py`

### Steps

1. Write a test that seeds a deterministic set of active Nova Outdoor products and is idempotent when called twice.
2. Run the test and confirm the expected failure.
3. Add a small seed collection covering chair, table, sofa, umbrella, and furniture set categories.
4. Implement idempotent insertion by SKU.
5. Run seed tests and the full suite.

### Expected

Seed initialization creates the same product set on every clean database and does not duplicate records on repeated execution.

## Task 4: Product query service

### Files

- `backend/src/tradepilot/services/products.py`
- `backend/tests/test_product_service.py`

### Steps

1. Write tests for case-insensitive keyword search across SKU/name/category/description, exact category filtering, active-only results, and result limits.
2. Run the tests and confirm the expected failure.
3. Implement a framework-independent `search_products` service function accepting a SQLAlchemy session and query parameters.
4. Run service tests and the full suite.

### Expected

Product retrieval logic is reusable by API routes and future Agent/tool integrations without importing FastAPI.

## Task 5: FastAPI application and API tests

### Files

- `backend/src/tradepilot/api.py`
- `backend/src/tradepilot/main.py`
- `backend/src/tradepilot/schemas.py`
- `backend/tests/test_api.py`

### Steps

1. Write API tests for `GET /health`, product listing, keyword/category filters, limit validation, and an empty result.
2. Run the API tests and confirm the expected failure.
3. Implement dependency-injected database sessions, response schemas, routes, and the FastAPI application.
4. Keep startup database creation separate from tests and provide an explicit local initialization path.
5. Run API tests and the full suite.

### Expected

The service returns stable JSON responses, validates inputs, and does not expose database internals through the API.

## Task 6: Developer workflow and verification

### Files

- `backend/README.md`
- `backend/ruff.toml` or Ruff configuration in `pyproject.toml`
- root `README.md` update if needed

### Steps

1. Add installation, test, lint, seed, and local run commands.
2. Run Ruff and fix only issues introduced by this phase.
3. Run the complete pytest suite from the backend directory.
4. Confirm generated database files and secrets are ignored.

### Expected

A fresh developer can install dependencies, run tests, initialize demo data, and start the API using documented commands.

## Completion checklist

- [ ] Backend package installs in editable mode.
- [ ] Product model and database tests pass.
- [ ] Seed data is deterministic and idempotent.
- [ ] Product service tests pass.
- [ ] API tests pass.
- [ ] Ruff passes.
- [ ] Documentation contains reproducible local commands.
- [ ] No secrets or generated database files are tracked.
