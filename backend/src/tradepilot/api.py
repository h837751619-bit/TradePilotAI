from __future__ import annotations

import logging
import os
import time
from typing import Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .customer import Customer, lookup_customer, search_customers, seed_customers  # noqa: F401
from .db import get_session, make_session_factory
from .email import generate_email_draft
from .evaluation import evaluate_dataset
from .inventory import Inventory, seed_inventory  # noqa: F401
from .models import AgentRun, Product, QuoteRecord  # noqa: F401
from .rate_limit import InMemoryRateLimiter
from .risk import assess_quote_risk
from .schemas import ProductResponse
from .seed import seed_products
from .services.products import search_products
from .workflow import create_quote_from_inquiry

logger = logging.getLogger("tradepilot.api")


class WorkflowRequest(BaseModel):
    inquiry: str = Field(min_length=1)
    customer_name: str = ""


def create_app(database_url: Optional[str] = None) -> FastAPI:
    database_url = database_url or os.getenv("DATABASE_URL", get_settings().database_url)
    settings = get_settings()
    rate_limiter = InMemoryRateLimiter(settings.workflow_rate_limit_per_minute)
    app = FastAPI(title="TradePilot AI API", version="0.1.0", docs_url="/docs" if settings.api_docs_enabled else None, redoc_url="/redoc" if settings.api_docs_enabled else None)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    @app.middleware("http")
    async def request_logging(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info("request method=%s path=%s status=%s duration_ms=%.1f", request.method, request.url.path, response.status_code, elapsed_ms)
        return response

    @app.exception_handler(HTTPException)
    async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return JSONResponse(status_code=exc.status_code, content={"error": {"code": f"HTTP_{exc.status_code}", "message": message}})

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"error": {"code": "VALIDATION_ERROR", "message": "Invalid request", "details": exc.errors()}})
    factory = make_session_factory(database_url)
    with factory() as session:
        seed_products(session)
        seed_inventory(session)
        seed_customers(session)

    def session_dependency():
        yield from get_session(factory)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/products", response_model=list[ProductResponse])
    def products(
        q: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = Query(default=20, ge=1, le=100),
        session: Session = Depends(session_dependency),  # noqa: B008
    ) -> list:
        return search_products(session, q=q, category=category, limit=limit)

    @app.post("/api/workflow/inquiry-to-quote")
    def inquiry_to_quote(request: Request, payload: WorkflowRequest, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        client_key = request.client.host if request.client else "unknown"
        if not rate_limiter.allow(client_key):
            raise HTTPException(status_code=429, detail="Workflow rate limit exceeded")
        try:
            result = create_quote_from_inquiry(session, payload.inquiry, payload.customer_name)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        risk = assess_quote_risk(result.quote)
        email = generate_email_draft(result.inquiry, result.quote)
        session.add(QuoteRecord(
            customer_name=result.quote.customer_name,
            inquiry_text=result.inquiry.raw_text,
            sku=result.quote.sku,
            quantity=result.quote.quantity,
            unit_price_usd=result.quote.unit_price_usd,
            total_price_usd=result.quote.total_price_usd,
            discount_percent=result.quote.discount_percent,
            status=result.quote.status,
        ))
        session.commit()
        quote_record = session.scalar(select(QuoteRecord).order_by(QuoteRecord.id.desc()))
        customer = lookup_customer(session, payload.customer_name) if payload.customer_name else None
        run_id = uuid4().hex[:12]
        session.add(AgentRun(
            run_id=run_id,
            inquiry_text=result.inquiry.raw_text,
            steps=[
                {"name": "Inquiry parsed", "status": "complete"},
                {"name": "Product search", "status": "complete"},
                {"name": "Inventory and pricing", "status": "complete"},
                {"name": "Quote generated", "status": "complete"},
                {"name": "Human approval", "status": "waiting"},
            ],
        ))
        session.commit()
        return {
            "run_id": run_id,
            "customer": {
                "matched": customer is not None,
                "company_name": customer.company_name if customer else payload.customer_name,
                "country": customer.country if customer else None,
                "contact_name": customer.contact_name if customer else None,
                "email": customer.email if customer else None,
            },
            "inquiry": {
                "raw_text": result.inquiry.raw_text,
                "quantity": result.inquiry.quantity,
                "destination_country": result.inquiry.destination_country,
                "project_type": result.inquiry.project_type,
                "product_keywords": result.inquiry.product_keywords,
            },
            "quote": {
                "id": quote_record.id,
                "customer_name": result.quote.customer_name,
                "sku": result.quote.sku,
                "quantity": result.quote.quantity,
                "unit_price_usd": result.quote.unit_price_usd,
                "total_price_usd": result.quote.total_price_usd,
                "discount_percent": result.quote.discount_percent,
                "inventory_sufficient": result.quote.inventory_sufficient,
                "status": result.quote.status,
            },
            "risk": {"requires_approval": risk.requires_approval, "reasons": risk.reasons},
            "email": {"subject": email.subject, "body": email.body, "status": email.status},
        }

    @app.get("/api/quotes")
    def quotes(session: Session = Depends(session_dependency)) -> list[dict]:  # noqa: B008
        records = session.scalars(select(QuoteRecord).order_by(QuoteRecord.id.desc())).all()
        return [
            {
                "id": record.id,
                "customer_name": record.customer_name,
                "inquiry_text": record.inquiry_text,
                "sku": record.sku,
                "quantity": record.quantity,
                "unit_price_usd": record.unit_price_usd,
                "total_price_usd": record.total_price_usd,
                "discount_percent": record.discount_percent,
                "status": record.status,
            }
            for record in records
        ]

    @app.get("/api/customers")
    def customers(q: Optional[str] = None, session: Session = Depends(session_dependency)) -> list[dict]:  # noqa: B008
        return [
            {"id": customer.id, "company_name": customer.company_name, "contact_name": customer.contact_name, "country": customer.country, "email": customer.email}
            for customer in search_customers(session, q)
        ]

    @app.post("/api/quotes/{quote_id}/approve")
    def approve_quote_endpoint(quote_id: int, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        record = session.get(QuoteRecord, quote_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Quote not found")
        if record.status != "draft":
            raise HTTPException(status_code=409, detail="Only draft quotes can be approved")
        record.status = "approved"
        session.commit()
        return {"id": record.id, "status": record.status}

    @app.get("/api/agent-runs")
    def agent_runs(session: Session = Depends(session_dependency)) -> list[dict]:  # noqa: B008
        records = session.scalars(select(AgentRun).order_by(AgentRun.id.desc())).all()
        return [{"run_id": record.run_id, "inquiry_text": record.inquiry_text, "steps": record.steps} for record in records]

    @app.get("/api/evaluation")
    def evaluation() -> dict:
        dataset = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/evaluation/inquiries.json"))
        return evaluate_dataset(dataset)

    return app
