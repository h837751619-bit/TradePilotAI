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

The catalog seed lives in `src/tradepilot/seed.py`; initial stock lives in
`src/tradepilot/inventory.py`. Both seeds are insert-only by SKU, so restarts
preserve product edits and manual stock adjustments. Add a product to both
files, rebuild the backend container, and the startup index calibration will
sync active MySQL products to Qdrant when semantic search is enabled.

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

Product retrieval supports a rule matcher and an optional semantic index. Set
`SEMANTIC_SEARCH_ENABLED=true`, `EMBEDDING_PROVIDER=huggingface`, and
`EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
to generate local embeddings with the CPU-friendly FastEmbed runtime.
The model is downloaded on first use, and its cache persists in the Compose
`tradepilot_embedding_cache` volume. Product vectors live in Qdrant; MySQL
remains authoritative for price, stock, MOQ, and quote state. Run
`POST /api/products/rebuild-semantic-index` as an admin after first enablement
or after switching embedding models. New, edited, and deactivated products
are synchronized automatically. The workflow response reports
`retrieval_mode` (`semantic`, `rules`, or `rules_fallback`). Without the optional
index, the existing rule matcher remains available.

When `RAG_EXPLANATIONS_ENABLED=true` and a chat provider is active, the workflow
sends only the retrieved candidate records and inquiry to that provider. The
response adds `explanation_mode`, provider/model metadata, a concise explanation,
the model's explanation for audit, and database-backed evidence fields to each
candidate. The displayed explanation is constructed from the selected fields and
current SQL values; this prevents an unsupported model claim from becoming a
product fact. Unknown SKUs and evidence fields are discarded. Provider failures
return `rules_fallback` explanations and do not interrupt product matching or
quote preview.

Endpoints:

- `GET /health`
- `GET /api/products?q=hotel`
- `GET /api/products?category=Outdoor%20Chair&limit=10`
- `GET /api/evaluation/rag?mode=rules`
- `GET /api/evaluation/rag?mode=semantic`

The RAG evaluation set is `data/evaluation/rag_inquiries.json`. It contains
English, Chinese, Italian, and Spanish paraphrases that deliberately avoid
the catalog's exact keywords. `top1_recall` measures whether the expected SKU
is ranked first, `top3_recall` measures whether it appears in the first three
candidates, and `mrr` measures the mean reciprocal rank. `misses` lists cases
where the expected SKU is absent from the first three results.
