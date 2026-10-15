from __future__ import annotations

import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Optional
from urllib.request import Request as UrlRequest
from urllib.request import urlopen
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select, text
from sqlalchemy.orm import Session

from .ai_provider import OllamaProvider, OpenAICompatibleProvider, parse_json_object
from .auth import (
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    issue_token,
    seed_auth_user,
    verify_password,
    verify_token_claims,
)
from .config import get_settings
from .customer import (
    Customer,
    extract_customer_name,
    lookup_customer,
    search_customers,
    seed_customers,
)
from .db import get_session, make_session_factory
from .email import generate_email_draft
from .evaluation import evaluate_dataset, evaluate_rag_dataset
from .inquiry import InquiryRequirements, parse_inquiry
from .inventory import (
    Inventory,
    InventoryAdjustment,
    InventoryMovement,
    deduct_reserved_inventory,
    release_reserved_inventory,
    reserve_inventory,
    seed_inventory,
)
from .models import (
    AgentRun,
    ApprovalHistory,
    EmbeddingRebuildJob,
    Product,
    QuoteRecord,
    RagEvaluationRun,
    RefreshToken,
    User,
)
from .product_matching import rank_product_candidates
from .quote import QuoteDraft
from .rag.explanations import (
    attach_ai_explanations,
    attach_fallback_explanations,
    explain_product_candidates,
)
from .rag.products import build_product_document
from .rag.reranker import ProductReranker
from .rag.vector_store import ProductVectorStore
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
    selected_sku: Optional[str] = None
    quantity: Optional[int] = Field(default=None, ge=1)
    destination_country: Optional[str] = None
    project_type: Optional[str] = None
    product_keywords: Optional[list[str]] = None
    budget_usd: Optional[float] = Field(default=None, ge=0)
    max_lead_time_days: Optional[int] = Field(default=None, ge=1)


class RagPlaygroundRequest(BaseModel):
    inquiry: str = Field(min_length=1)
    mode: str = Field(default="semantic", pattern="^(rules|semantic)$")
    top_k: int = Field(default=5, ge=1, le=20)
    score_threshold: float = Field(default=0.45, ge=0, le=1)


class CustomerPayload(BaseModel):
    company_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    contact_name: Optional[str] = Field(default=None, max_length=120)
    country: Optional[str] = Field(default=None, max_length=80)
    email: Optional[str] = Field(default=None, max_length=200)


class AIProviderRequest(BaseModel):
    provider: str = Field(pattern="^(rules|ollama|openai_compatible|deepseek|kimi)$")


class AIProviderConfigUpdate(BaseModel):
    provider: str = Field(pattern="^(rules|ollama|openai_compatible|deepseek|kimi)$")
    base_url: Optional[str] = Field(default=None, min_length=1, max_length=500)
    model: Optional[str] = Field(default=None, min_length=1, max_length=200)
    timeout_seconds: Optional[float] = Field(default=None, gt=0, le=300)
    # Write-only by contract: this value is applied in memory and never returned.
    api_key: Optional[str] = Field(default=None, max_length=500)


class EmbeddingProfileRequest(BaseModel):
    profile_id: str = Field(min_length=1, max_length=200)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=200)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=300)


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=1, max_length=120, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=200)
    role: str = Field(default="viewer", pattern="^(admin|approver|viewer)$")


class UserUpdateRequest(BaseModel):
    role: Optional[str] = Field(default=None, pattern="^(admin|approver|viewer)$")
    password: Optional[str] = Field(default=None, min_length=8, max_length=200)
    is_active: Optional[bool] = None


class ProductUpdate(BaseModel):
    material: Optional[str] = Field(default=None, max_length=200)
    colors: Optional[str] = Field(default=None, max_length=200)
    match_tags: Optional[str] = Field(default=None, max_length=500)
    min_order_quantity: Optional[int] = Field(default=None, ge=1)
    lead_time_days: Optional[int] = Field(default=None, ge=1)
    unit_price_usd: Optional[float] = Field(default=None, gt=0)
    is_active: Optional[bool] = None


class InventoryUpdate(BaseModel):
    on_hand_quantity: int = Field(ge=0)
    reason: str = Field(default="manual adjustment", min_length=1, max_length=300)


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=100)
    description: str = ""
    material: str = ""
    colors: str = ""
    match_tags: str = ""
    min_order_quantity: int = Field(default=1, ge=1)
    lead_time_days: int = Field(default=1, ge=1)
    unit_price_usd: float = Field(gt=0)
    is_active: bool = True


def create_app(database_url: Optional[str] = None) -> FastAPI:
    database_url = database_url or os.getenv("DATABASE_URL", get_settings().database_url)
    settings = get_settings()
    rate_limiter = InMemoryRateLimiter(settings.workflow_rate_limit_per_minute)
    configured_ai_provider = settings.ai_provider
    if configured_ai_provider in {"openai_compatible", "deepseek", "kimi"} and not getattr(settings, f"{configured_ai_provider}_api_key").strip():
        configured_ai_provider = "rules"
    active_ai_provider = {"value": configured_ai_provider}
    active_embedding_profile = {"id": f"{settings.embedding_provider}:{settings.embedding_model}", "provider": settings.embedding_provider, "model": settings.embedding_model}
    embedding_jobs: dict[str, dict] = {}
    embedding_jobs_lock = Lock()
    embedding_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="embedding-rebuild")
    index_rebuild_lock = Lock()
    index_rebuild_state = {"queued": False}
    vector_store = ProductVectorStore(
        settings.ollama_base_url, settings.qdrant_url, settings.embedding_model, settings.qdrant_collection,
        settings.semantic_search_timeout_seconds, settings.embedding_provider,
    ) if settings.semantic_search_enabled else None
    reranker = ProductReranker(settings.reranker_model, settings.reranker_enabled)

    def sync_product_index(product: Product) -> None:
        if vector_store is not None:
            try:
                if product.is_active:
                    vector_store.upsert_product(product)
                else:
                    vector_store.delete_product(product.sku)
            except (OSError, ValueError, KeyError, ImportError, RuntimeError, json.JSONDecodeError):
                logger.exception("Product vector index sync failed for sku=%s", product.sku)
                schedule_index_rebuild(f"product sync failed for {product.sku}")

    def make_ai_provider(provider_id: str, *, tag_generation: bool = False):
        if provider_id == "ollama":
            return OllamaProvider(
                settings.ollama_base_url,
                settings.ollama_model,
                timeout=settings.ollama_tag_timeout_seconds if tag_generation else 30.0,
                think=False if tag_generation else settings.ollama_think,
            )
        if provider_id == "openai_compatible" and settings.openai_compatible_api_key.strip():
            provider = OpenAICompatibleProvider(
                settings.openai_compatible_api_key,
                settings.openai_compatible_base_url,
                settings.openai_compatible_model,
                timeout=settings.openai_compatible_timeout_seconds,
            )
            provider.name = provider_id
            return provider
        if provider_id in {"deepseek", "kimi"}:
            api_key = getattr(settings, f"{provider_id}_api_key").strip()
            if api_key:
                provider = OpenAICompatibleProvider(
                    api_key,
                    getattr(settings, f"{provider_id}_base_url"),
                    getattr(settings, f"{provider_id}_model"),
                    timeout=getattr(settings, f"{provider_id}_timeout_seconds"),
                )
                provider.name = provider_id
                return provider
        return None

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
        seed_auth_user(session, settings.auth_username, settings.auth_password_hash, settings.auth_role)
        interrupted_jobs = session.scalars(select(EmbeddingRebuildJob).where(EmbeddingRebuildJob.status.in_(["queued", "running"]))).all()
        for interrupted in interrupted_jobs:
            interrupted.status = "failed"
            interrupted.error = "Embedding rebuild interrupted by service restart"
        if interrupted_jobs:
            session.commit()

    def session_dependency():
        yield from get_session(factory)

    def schedule_index_rebuild(reason: str) -> None:
        """Queue one eventual-consistency rebuild after a product sync failure."""
        if vector_store is None:
            return
        with index_rebuild_lock:
            if index_rebuild_state["queued"]:
                return
            index_rebuild_state["queued"] = True

        def rebuild() -> None:
            try:
                with factory() as rebuild_session:
                    vector_store.rebuild(rebuild_session)
                logger.info("Product vector index reconciled after %s", reason)
            except (OSError, ValueError, KeyError, ImportError, RuntimeError, json.JSONDecodeError):
                logger.exception("Product vector index reconciliation failed after %s", reason)
            finally:
                with index_rebuild_lock:
                    index_rebuild_state["queued"] = False

        embedding_executor.submit(rebuild)

    @app.on_event("startup")
    async def reconcile_product_index_on_startup() -> None:
        # Compose deployments can have MySQL and Qdrant volumes restored independently.
        # Reconcile once in the background so a stale vector index cannot persist across restarts.
        if vector_store is not None and settings.app_env == "docker":
            schedule_index_rebuild("service startup")

    def unique_quote_records(records: list[QuoteRecord]) -> list[QuoteRecord]:
        seen: set[tuple] = set()
        unique: list[QuoteRecord] = []
        for record in records:
            signature = (
                record.customer_name,
                record.inquiry_text,
                record.sku,
                record.quantity,
                record.unit_price_usd,
                record.total_price_usd,
                record.discount_percent,
            )
            if signature not in seen:
                seen.add(signature)
                unique.append(record)
        return unique

    def require_user(request: Request, session: Session, roles: set[str]) -> User:
        if not settings.auth_enabled or not settings.auth_secret:
            raise HTTPException(status_code=503, detail="Authentication is not enabled")
        authorization = request.headers.get("authorization", "")
        token = authorization.removeprefix("Bearer ").strip()
        claims = verify_token_claims(token, settings.auth_secret) if token else None
        if not claims:
            raise HTTPException(status_code=401, detail="Valid bearer token required")
        user = session.scalar(select(User).where(User.username == claims["sub"], User.is_active.is_(True)))
        if user is None:
            raise HTTPException(status_code=401, detail="User is inactive or missing")
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user

    def authorize_if_enabled(
        request: Request,
        session: Session,
        roles: set[str] | None = None,
    ) -> User | None:
        if not settings.auth_enabled:
            return None
        return require_user(request, session, roles or {"admin", "approver", "viewer"})

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/auth/login")
    def login(payload: LoginRequest, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        if not settings.auth_enabled or not settings.auth_secret:
            raise HTTPException(status_code=503, detail="Authentication is not enabled")
        user = session.scalar(select(User).where(User.username == payload.username, User.is_active.is_(True)))
        if user is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        refresh_token = create_refresh_token()
        session.add(RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=settings.auth_refresh_ttl_seconds),
        ))
        session.commit()
        return {
            "access_token": issue_token(user.username, settings.auth_secret, settings.auth_token_ttl_seconds, user.role),
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.auth_token_ttl_seconds,
            "refresh_expires_in": settings.auth_refresh_ttl_seconds,
            "role": user.role,
        }

    @app.post("/api/auth/refresh")
    def refresh(payload: RefreshRequest, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        if not settings.auth_enabled or not settings.auth_secret:
            raise HTTPException(status_code=503, detail="Authentication is not enabled")
        record = session.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(payload.refresh_token)))
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if record is None or record.revoked_at is not None or record.expires_at <= now:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        user = session.scalar(select(User).where(User.id == record.user_id, User.is_active.is_(True)))
        if user is None:
            raise HTTPException(status_code=401, detail="User is inactive or missing")
        record.revoked_at = now
        next_refresh = create_refresh_token()
        session.add(RefreshToken(user_id=user.id, token_hash=hash_refresh_token(next_refresh), expires_at=now + timedelta(seconds=settings.auth_refresh_ttl_seconds)))
        session.commit()
        return {
            "access_token": issue_token(user.username, settings.auth_secret, settings.auth_token_ttl_seconds, user.role),
            "refresh_token": next_refresh,
            "token_type": "bearer",
            "expires_in": settings.auth_token_ttl_seconds,
            "refresh_expires_in": settings.auth_refresh_ttl_seconds,
            "role": user.role,
        }

    @app.post("/api/auth/logout")
    def logout(payload: RefreshRequest, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        record = session.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(payload.refresh_token)))
        if record is not None and record.revoked_at is None:
            record.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
            session.commit()
        return {"ok": True}

    @app.get("/api/auth/status")
    def auth_status() -> dict:
        return {"enabled": settings.auth_enabled}

    @app.get("/api/users")
    def users(request: Request, session: Session = Depends(session_dependency)) -> list[dict]:  # noqa: B008
        require_user(request, session, {"admin"})
        records = session.scalars(select(User).order_by(User.username.asc())).all()
        return [{"id": user.id, "username": user.username, "role": user.role, "is_active": user.is_active} for user in records]

    @app.post("/api/users", status_code=201)
    def create_user(payload: UserCreateRequest, request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        require_user(request, session, {"admin"})
        if session.scalar(select(User).where(User.username == payload.username)):
            raise HTTPException(status_code=409, detail="Username already exists")
        user = User(username=payload.username, password_hash=hash_password(payload.password), role=payload.role, is_active=True)
        session.add(user)
        session.commit()
        session.refresh(user)
        return {"id": user.id, "username": user.username, "role": user.role, "is_active": user.is_active}

    @app.patch("/api/users/{user_id}")
    def update_user(user_id: int, payload: UserUpdateRequest, request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        admin = require_user(request, session, {"admin"})
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if user.id == admin.id and payload.is_active is False:
            raise HTTPException(status_code=400, detail="Administrator cannot deactivate self")
        if payload.role is not None:
            user.role = payload.role
        if payload.password is not None:
            user.password_hash = hash_password(payload.password)
        if payload.is_active is not None:
            user.is_active = payload.is_active
        session.commit()
        session.refresh(user)
        return {"id": user.id, "username": user.username, "role": user.role, "is_active": user.is_active}

    @app.get("/api/ai/providers")
    def ai_providers(request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session)
        return {
            "active": active_ai_provider["value"],
            "providers": [
                {"id": "rules", "name": "Rule engine", "available": True},
                {"id": "ollama", "name": "Ollama / Qwen", "model": settings.ollama_model, "available": True},
                {
                    "id": "openai_compatible",
                    "name": "Online model API",
                    "model": settings.openai_compatible_model,
                    "available": bool(settings.openai_compatible_api_key.strip()),
                },
                {"id": "deepseek", "name": "DeepSeek", "model": settings.deepseek_model, "available": bool(settings.deepseek_api_key.strip())},
                {"id": "kimi", "name": "Kimi / Moonshot", "model": settings.kimi_model, "available": bool(settings.kimi_api_key.strip())},
            ],
        }

    @app.get("/api/settings/ai")
    def ai_settings(request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session)
        provider_specs = [
            ("rules", "Rule engine", "", "", None, None),
            ("ollama", "Ollama / Qwen", settings.ollama_base_url, settings.ollama_model, None, settings.ollama_tag_timeout_seconds),
            ("openai_compatible", "Online model API", settings.openai_compatible_base_url, settings.openai_compatible_model, settings.openai_compatible_api_key, settings.openai_compatible_timeout_seconds),
            ("deepseek", "DeepSeek", settings.deepseek_base_url, settings.deepseek_model, settings.deepseek_api_key, settings.deepseek_timeout_seconds),
            ("kimi", "Kimi / Moonshot", settings.kimi_base_url, settings.kimi_model, settings.kimi_api_key, settings.kimi_timeout_seconds),
        ]
        return {
            "active": active_ai_provider["value"],
            "providers": [
                {
                    "id": provider_id,
                    "name": name,
                    "base_url": base_url,
                    "model": model,
                    "timeout_seconds": timeout,
                    "api_key_configured": bool(api_key.strip()) if isinstance(api_key, str) else False,
                    "available": provider_id in {"rules", "ollama"} or bool(api_key and api_key.strip()),
                }
                for provider_id, name, base_url, model, api_key, timeout in provider_specs
            ],
            "api_key_storage": "runtime_only",
        }

    @app.patch("/api/settings/ai")
    def update_ai_settings(payload: AIProviderConfigUpdate, request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session, {"admin"})
        provider = payload.provider
        prefix = "openai_compatible" if provider == "openai_compatible" else provider
        if payload.base_url is not None and provider != "rules":
            setattr(settings, f"{prefix}_base_url", payload.base_url.strip().rstrip("/"))
        if payload.model is not None and provider != "rules":
            setattr(settings, f"{prefix}_model", payload.model.strip())
        if payload.timeout_seconds is not None and provider != "rules":
            timeout_attr = "ollama_tag_timeout_seconds" if provider == "ollama" else f"{prefix}_timeout_seconds"
            setattr(settings, timeout_attr, payload.timeout_seconds)
        if payload.api_key is not None and provider in {"openai_compatible", "deepseek", "kimi"}:
            setattr(settings, f"{prefix}_api_key", payload.api_key.strip())
        if provider in {"openai_compatible", "deepseek", "kimi"} and not getattr(settings, f"{prefix}_api_key").strip():
            if active_ai_provider["value"] == provider:
                active_ai_provider["value"] = "rules"
        elif provider == "rules":
            active_ai_provider["value"] = "rules"
        else:
            active_ai_provider["value"] = provider
        return {"active": active_ai_provider["value"], "updated": provider, "api_key_configured": bool(getattr(settings, f"{prefix}_api_key", "").strip()) if provider in {"openai_compatible", "deepseek", "kimi"} else False}

    @app.post("/api/settings/ai/test")
    def test_ai_connection(payload: AIProviderRequest, request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session, {"admin"})
        started = time.perf_counter()
        if payload.provider == "rules":
            return {"provider": "rules", "success": True, "model": "rules-v1", "latency_ms": 0, "message": "Rule engine is ready"}
        try:
            provider = make_ai_provider(payload.provider, tag_generation=True)
            if provider is None:
                return {"provider": payload.provider, "success": False, "model": None, "latency_ms": round((time.perf_counter() - started) * 1000), "message": "Provider is not configured"}
            response = provider.complete("Reply with OK only.")
            return {"provider": payload.provider, "success": True, "model": response.model, "latency_ms": round((time.perf_counter() - started) * 1000), "message": "Connection succeeded"}
        except (OSError, TimeoutError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            logger.warning("AI provider connection test failed for %s: %s", payload.provider, exc)
            return {"provider": payload.provider, "success": False, "model": getattr(settings, f"{payload.provider}_model", None), "latency_ms": round((time.perf_counter() - started) * 1000), "message": f"Connection failed: {exc}"}

    @app.get("/api/settings/ai/diagnostics")
    def ai_diagnostics(request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session)
        checks: list[dict] = []

        started = time.perf_counter()
        try:
            session.execute(text("SELECT 1"))
            checks.append({"id": "mysql", "name": "MySQL", "status": "ok", "latency_ms": round((time.perf_counter() - started) * 1000), "message": "Database connection is healthy"})
        except Exception as exc:  # noqa: BLE001
            logger.warning("MySQL diagnostics failed: %s", exc)
            checks.append({"id": "mysql", "name": "MySQL", "status": "error", "latency_ms": round((time.perf_counter() - started) * 1000), "message": "Database connection failed"})

        if settings.semantic_search_enabled:
            started = time.perf_counter()
            try:
                with urlopen(UrlRequest(f"{settings.qdrant_url.rstrip('/')}/collections"), timeout=3.0) as response:
                    response.read(1)
                checks.append({"id": "qdrant", "name": "Qdrant", "status": "ok", "latency_ms": round((time.perf_counter() - started) * 1000), "message": "Vector service is reachable"})
            except (OSError, TimeoutError, ValueError) as exc:
                logger.warning("Qdrant diagnostics failed: %s", exc)
                checks.append({"id": "qdrant", "name": "Qdrant", "status": "error", "latency_ms": round((time.perf_counter() - started) * 1000), "message": "Vector service is unreachable"})
        else:
            checks.append({"id": "qdrant", "name": "Qdrant", "status": "disabled", "latency_ms": 0, "message": "Semantic search is disabled"})

        if settings.ollama_base_url.strip():
            started = time.perf_counter()
            try:
                with urlopen(UrlRequest(f"{settings.ollama_base_url.rstrip('/')}/api/tags"), timeout=3.0) as response:
                    response.read(1)
                checks.append({"id": "ollama", "name": "Ollama", "status": "ok", "latency_ms": round((time.perf_counter() - started) * 1000), "message": f"Endpoint reachable ({settings.ollama_model})"})
            except (OSError, TimeoutError, ValueError) as exc:
                logger.warning("Ollama diagnostics failed: %s", exc)
                checks.append({"id": "ollama", "name": "Ollama", "status": "error", "latency_ms": round((time.perf_counter() - started) * 1000), "message": "Endpoint is unreachable"})

        online_provider_ids = ("openai_compatible", "deepseek", "kimi")
        for provider_id in online_provider_ids:
            configured = bool(getattr(settings, f"{provider_id}_api_key").strip())
            checks.append({"id": provider_id, "name": provider_id, "status": "configured" if configured else "not_configured", "latency_ms": 0, "message": "API key configured; use Test connection to verify endpoint" if configured else "API key is not configured"})
        return {"active": active_ai_provider["value"], "checks": checks}

    @app.post("/api/ai/providers")
    def set_ai_provider(payload: AIProviderRequest, request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session, {"admin"})
        if payload.provider in {"openai_compatible", "deepseek", "kimi"} and not getattr(settings, f"{payload.provider}_api_key").strip():
            raise HTTPException(status_code=400, detail=f"{payload.provider} API key is not configured on the server")
        active_ai_provider["value"] = payload.provider
        return {"active": payload.provider}

    @app.get("/api/products", response_model=list[ProductResponse])
    def products(
        request: Request,
        q: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = Query(default=20, ge=1, le=100),
        include_inactive: bool = False,
        session: Session = Depends(session_dependency),  # noqa: B008
    ) -> list:
        authorize_if_enabled(request, session)
        records = search_products(session, q=q, category=category, limit=limit, include_inactive=include_inactive)
        inventory_by_sku = {item.sku: item for item in session.scalars(select(Inventory)).all()}
        return [
            {
                "id": product.id,
                "sku": product.sku,
                "name": product.name,
                "category": product.category,
                "description": product.description,
                "material": product.material,
                "colors": product.colors,
                "match_tags": product.match_tags,
                "min_order_quantity": product.min_order_quantity,
                "lead_time_days": product.lead_time_days,
                "unit_price_usd": product.unit_price_usd,
                "is_active": product.is_active,
                "on_hand_quantity": inventory_by_sku.get(product.sku).on_hand_quantity if inventory_by_sku.get(product.sku) else 0,
                "reserved_quantity": inventory_by_sku.get(product.sku).reserved_quantity if inventory_by_sku.get(product.sku) else 0,
                "available_quantity": (inventory_by_sku.get(product.sku).on_hand_quantity - inventory_by_sku.get(product.sku).reserved_quantity) if inventory_by_sku.get(product.sku) else 0,
            }
            for product in records
        ]

    @app.get("/api/products/{sku}/inventory/movements")
    def product_inventory_movements(sku: str, request: Request, session: Session = Depends(session_dependency)) -> list[dict]:  # noqa: B008
        authorize_if_enabled(request, session)
        if session.scalar(select(Product).where(Product.sku == sku)) is None:
            raise HTTPException(status_code=404, detail="Product not found")
        movements = [
            {
                "id": item.id,
                "quote_id": item.quote_id,
                "sku": item.sku,
                "quantity": item.quantity,
                "movement_type": item.movement_type,
                "actor": item.actor,
                "reason": None,
                "previous_quantity": None,
                "new_quantity": None,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in session.scalars(
                select(InventoryMovement)
                .where(InventoryMovement.sku == sku)
                .order_by(InventoryMovement.created_at.desc(), InventoryMovement.id.desc())
            ).all()
        ]
        movements.extend(
            {
                "id": item.id,
                "quote_id": None,
                "sku": item.sku,
                "quantity": item.new_quantity - item.previous_quantity,
                "movement_type": "adjustment",
                "actor": item.actor,
                "reason": item.reason,
                "previous_quantity": item.previous_quantity,
                "new_quantity": item.new_quantity,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in session.scalars(
                select(InventoryAdjustment)
                .where(InventoryAdjustment.sku == sku)
                .order_by(InventoryAdjustment.created_at.desc(), InventoryAdjustment.id.desc())
            ).all()
        )
        return sorted(movements, key=lambda item: (item["created_at"] or "", item["id"]), reverse=True)

    @app.patch("/api/products/{sku}")
    def update_product(sku: str, payload: ProductUpdate, request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session, {"admin", "approver"})
        product = session.scalar(select(Product).where(Product.sku == sku))
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        session.commit()
        session.refresh(product)
        sync_product_index(product)
        return {"id": product.id, "sku": product.sku, "name": product.name, "material": product.material, "colors": product.colors, "match_tags": product.match_tags, "min_order_quantity": product.min_order_quantity, "lead_time_days": product.lead_time_days, "unit_price_usd": product.unit_price_usd, "is_active": product.is_active}

    @app.patch("/api/products/{sku}/inventory")
    def update_inventory(sku: str, payload: InventoryUpdate, request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        user = authorize_if_enabled(request, session, {"admin", "approver"})
        if session.scalar(select(Product).where(Product.sku == sku)) is None:
            raise HTTPException(status_code=404, detail="Product not found")
        inventory = session.scalar(select(Inventory).where(Inventory.sku == sku).with_for_update())
        previous_quantity = inventory.on_hand_quantity if inventory is not None else 0
        if inventory is None:
            inventory = Inventory(sku=sku, on_hand_quantity=payload.on_hand_quantity, reserved_quantity=0)
            session.add(inventory)
        elif payload.on_hand_quantity < inventory.reserved_quantity:
            raise HTTPException(status_code=409, detail=f"On-hand quantity cannot be below reserved quantity ({inventory.reserved_quantity})")
        else:
            inventory.on_hand_quantity = payload.on_hand_quantity
        actor = user.username if user else (request.headers.get("x-actor-id", "manual").strip()[:120] or "manual")
        if previous_quantity != payload.on_hand_quantity:
            session.add(InventoryAdjustment(
                sku=sku,
                previous_quantity=previous_quantity,
                new_quantity=payload.on_hand_quantity,
                reason=payload.reason.strip(),
                actor=actor,
            ))
        session.commit()
        session.refresh(inventory)
        return {"sku": sku, "on_hand_quantity": inventory.on_hand_quantity, "reserved_quantity": inventory.reserved_quantity, "available_quantity": inventory.on_hand_quantity - inventory.reserved_quantity}

    @app.post("/api/products/{sku}/suggest-tags")
    def suggest_product_tags(sku: str, request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session, {"admin", "approver"})
        product = session.scalar(select(Product).where(Product.sku == sku))
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        active_provider = active_ai_provider["value"]
        if active_provider == "rules":
            return {"sku": sku, "provider": "rules", "suggestions": [product.category.lower(), product.material.lower()]}
        prompt = f"Return JSON only as {{\"tags\":[...]}}, 5 concise English product search synonyms. Product: {product.name}. Category: {product.category}. Description: {product.description}. Material: {product.material}. Existing tags: {product.match_tags}"
        try:
            provider = make_ai_provider(active_provider, tag_generation=True)
            if provider is None:
                raise ValueError("Selected AI provider is not configured")
            result = provider.complete(prompt)
            data = parse_json_object(result.text)
            suggestions = [str(tag).strip().lower() for tag in data.get("tags", []) if str(tag).strip()]
            return {"sku": sku, "provider": result.provider, "model": result.model, "suggestions": list(dict.fromkeys(suggestions))[:10]}
        except (OSError, TimeoutError, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=503, detail=f"AI tag suggestion unavailable: {exc}") from exc

    @app.post("/api/products", status_code=201)
    def create_product(payload: ProductCreate, request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session, {"admin", "approver"})
        if session.scalar(select(Product).where(Product.sku == payload.sku)):
            raise HTTPException(status_code=409, detail="Product SKU already exists")
        product = Product(**payload.model_dump())
        session.add(product)
        session.commit()
        session.refresh(product)
        sync_product_index(product)
        return {"id": product.id, "sku": product.sku, "name": product.name, "category": product.category, "description": product.description, "material": product.material, "colors": product.colors, "match_tags": product.match_tags, "min_order_quantity": product.min_order_quantity, "lead_time_days": product.lead_time_days, "unit_price_usd": product.unit_price_usd, "is_active": product.is_active}

    @app.delete("/api/products/{sku}", status_code=204)
    def delete_product(sku: str, request: Request, session: Session = Depends(session_dependency)) -> None:  # noqa: B008
        authorize_if_enabled(request, session, {"admin", "approver"})
        product = session.scalar(select(Product).where(Product.sku == sku))
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        product.is_active = False
        session.commit()

        sync_product_index(product)

    @app.post("/api/products/rebuild-semantic-index")
    def rebuild_semantic_index(request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session, {"admin"})
        if vector_store is None:
            raise HTTPException(status_code=409, detail="Semantic search is not enabled")
        try:
            count = vector_store.rebuild(session)
        except (OSError, ValueError, KeyError, ImportError, RuntimeError, json.JSONDecodeError) as exc:
            logger.exception("Product vector index rebuild failed")
            raise HTTPException(status_code=503, detail="Semantic index unavailable") from exc
        return {"indexed_products": count, "embedding_model": active_embedding_profile["model"]}

    @app.get("/api/settings/embeddings")
    def embedding_settings(request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session)
        return {"active": active_embedding_profile, "profiles": settings.embedding_profile_options}

    @app.get("/api/settings/embeddings/jobs/{job_id}")
    def embedding_job_status(job_id: str, request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session)
        record = session.scalar(select(EmbeddingRebuildJob).where(EmbeddingRebuildJob.job_id == job_id))
        if record is None:
            raise HTTPException(status_code=404, detail="Embedding job not found")
        return {"job_id": record.job_id, "status": record.status, "profile": {"id": record.profile_id, "provider": record.embedding_provider, "model": record.embedding_model}, "indexed_products": record.indexed_products, "processed_products": record.processed_products, "total_products": record.total_products, "progress_percent": record.progress_percent, "error": record.error}

    @app.get("/api/settings/embeddings/jobs")
    def embedding_job_history(request: Request, limit: int = Query(default=20, ge=1, le=100), offset: int = Query(default=0, ge=0), session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session)
        total = session.scalar(select(func.count()).select_from(EmbeddingRebuildJob)) or 0
        records = session.scalars(select(EmbeddingRebuildJob).order_by(desc(EmbeddingRebuildJob.created_at)).offset(offset).limit(limit)).all()
        items = [{"job_id": record.job_id, "status": record.status, "profile": {"id": record.profile_id, "provider": record.embedding_provider, "model": record.embedding_model}, "indexed_products": record.indexed_products, "processed_products": record.processed_products, "total_products": record.total_products, "progress_percent": record.progress_percent, "error": record.error, "created_at": record.created_at.isoformat(), "updated_at": record.updated_at.isoformat()} for record in records]
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    @app.post("/api/settings/embeddings")
    def switch_embedding_profile(payload: EmbeddingProfileRequest, request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session, {"admin"})
        profile = next((item for item in settings.embedding_profile_options if item["id"] == payload.profile_id), None)
        if profile is None:
            raise HTTPException(status_code=404, detail="Embedding profile not configured")
        if not settings.semantic_search_enabled:
            raise HTTPException(status_code=409, detail="Semantic search is not enabled")
        with embedding_jobs_lock:
            if any(job["status"] in {"queued", "running"} for job in embedding_jobs.values()):
                raise HTTPException(status_code=409, detail="Another embedding rebuild is already running")
            job_id = str(uuid4())
            embedding_jobs[job_id] = {"status": "queued", "profile": profile, "indexed_products": None, "processed_products": 0, "total_products": None, "progress_percent": 0, "error": None}
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        session.add(EmbeddingRebuildJob(job_id=job_id, profile_id=profile["id"], embedding_provider=profile["provider"], embedding_model=profile["model"], status="queued", created_at=now, updated_at=now))
        session.commit()

        def update_job_state(**updates: object) -> None:
            with embedding_jobs_lock:
                embedding_jobs[job_id].update(updates)
            with factory() as state_session:
                state_record = state_session.scalar(select(EmbeddingRebuildJob).where(EmbeddingRebuildJob.job_id == job_id))
                if state_record is None:
                    return
                for key, value in updates.items():
                    setattr(state_record, key, value)
                state_record.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                state_session.commit()

        def rebuild_embedding_job() -> None:
            nonlocal vector_store
            update_job_state(status="running")
            try:
                candidate_store = ProductVectorStore(
                    settings.ollama_base_url, settings.qdrant_url, profile["model"], settings.qdrant_collection,
                    settings.semantic_search_timeout_seconds, profile["provider"],
                )
                def update_progress(processed: int, total: int) -> None:
                    update_job_state(processed_products=processed, total_products=total, progress_percent=round(processed / total * 100) if total else 100)

                with factory() as worker_session:
                    indexed = candidate_store.rebuild(worker_session, progress_callback=update_progress)
                vector_store = candidate_store
                active_embedding_profile.update(profile)
                update_job_state(status="succeeded", indexed_products=indexed, progress_percent=100)
            except (OSError, ValueError, KeyError, ImportError, RuntimeError, json.JSONDecodeError) as exc:
                logger.exception("Embedding profile switch failed")
                update_job_state(status="failed", error=str(exc))

        embedding_executor.submit(rebuild_embedding_job)
        return {"job_id": job_id, "status": "queued", "profile": profile}

    @app.post("/api/workflow/inquiry-to-quote")
    def inquiry_to_quote(request: Request, payload: WorkflowRequest, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session, {"admin", "approver"})
        client_key = request.client.host if request.client else "unknown"
        if not rate_limiter.allow(client_key):
            raise HTTPException(status_code=429, detail="Workflow rate limit exceeded")
        try:
            customer_name = payload.customer_name.strip() or extract_customer_name(payload.inquiry)
            provider = make_ai_provider(active_ai_provider["value"])
            cached_selection = payload.selected_sku is not None and payload.quantity is not None
            parsed_inquiry = None
            if cached_selection:
                parsed_inquiry = InquiryRequirements(
                    raw_text=payload.inquiry,
                    quantity=payload.quantity,
                    destination_country=payload.destination_country,
                    project_type=payload.project_type,
                    product_keywords=payload.product_keywords or [],
                    budget_usd=payload.budget_usd,
                    max_lead_time_days=payload.max_lead_time_days,
                    ai_provider=active_ai_provider["value"],
                )
            semantic_matches = None
            retrieval_mode = "rules"
            if vector_store is not None and not cached_selection:
                try:
                    semantic_matches = vector_store.search(payload.inquiry)
                    retrieval_mode = "semantic" if semantic_matches else "rules"
                except (OSError, ValueError, KeyError, ImportError, RuntimeError, json.JSONDecodeError):
                    logger.exception("Product semantic search failed; using rule matching")
                    retrieval_mode = "rules_fallback"
            result = create_quote_from_inquiry(
                session, payload.inquiry, customer_name, provider, payload.selected_sku,
                semantic_matches=semantic_matches, parsed_inquiry=parsed_inquiry,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        product_matches = rank_product_candidates(
            session,
            result.inquiry.product_keywords,
            result.inquiry.quantity,
            result.inquiry.project_type,
            budget_usd=result.inquiry.budget_usd,
            max_lead_time_days=result.inquiry.max_lead_time_days,
            keyword_weight=settings.product_keyword_weight,
            project_weight=settings.product_project_weight,
            quantity_weight=settings.product_quantity_weight,
            semantic_matches=semantic_matches,
        )
        explanation_mode = "rules"
        explanation_provider = "rules"
        explanation_model = None
        attach_fallback_explanations(product_matches)
        if not cached_selection and settings.rag_explanations_enabled and provider is not None and product_matches:
            try:
                explanations, explanation_provider, explanation_model = explain_product_candidates(
                    session, result.inquiry.raw_text, product_matches, provider
                )
                attach_ai_explanations(product_matches, explanations)
                explanation_mode = "grounded_ai"
            except (OSError, TimeoutError, ValueError, TypeError, KeyError, json.JSONDecodeError):
                logger.exception("Grounded product explanation failed; using rule explanations")
                explanation_mode = "rules_fallback"
        risk = assess_quote_risk(result.quote)
        email = generate_email_draft(result.inquiry, result.quote)
        quote_record = None
        if payload.selected_sku:
            quote_record = session.scalar(
                select(QuoteRecord)
                .where(
                    QuoteRecord.customer_name == result.quote.customer_name,
                    QuoteRecord.inquiry_text == result.inquiry.raw_text,
                    QuoteRecord.sku == result.quote.sku,
                    QuoteRecord.quantity == result.quote.quantity,
                    QuoteRecord.unit_price_usd == result.quote.unit_price_usd,
                    QuoteRecord.total_price_usd == result.quote.total_price_usd,
                    QuoteRecord.discount_percent == result.quote.discount_percent,
                )
                .order_by(QuoteRecord.id.desc())
            )
            if quote_record is None:
                quote_record = QuoteRecord(
                    customer_name=result.quote.customer_name,
                    inquiry_text=result.inquiry.raw_text,
                    sku=result.quote.sku,
                    quantity=result.quote.quantity,
                    unit_price_usd=result.quote.unit_price_usd,
                    total_price_usd=result.quote.total_price_usd,
                    discount_percent=result.quote.discount_percent,
                    status=result.quote.status,
                )
                session.add(quote_record)
                session.flush()
            else:
                session.refresh(quote_record)
            if quote_record.status == "draft":
                reserve_inventory(session, quote_record.id, quote_record.sku, quote_record.quantity)
            session.commit()
        risk_requires_approval = quote_record is not None and quote_record.status != "approved" and risk.requires_approval
        customer = lookup_customer(session, customer_name) if customer_name else None
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
            "retrieval_mode": retrieval_mode,
            "explanation_mode": explanation_mode,
            "explanation_provider": explanation_provider,
            "explanation_model": explanation_model,
            "customer": {
                "matched": customer is not None,
                "company_name": customer.company_name if customer else customer_name,
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
                "budget_usd": result.inquiry.budget_usd,
                "max_lead_time_days": result.inquiry.max_lead_time_days,
                "ai_provider": result.inquiry.ai_provider,
            },
            "product_matches": product_matches,
            "quote": {
                "id": quote_record.id if quote_record else None,
                "customer_name": result.quote.customer_name,
                "sku": result.quote.sku,
                "quantity": result.quote.quantity,
                "unit_price_usd": result.quote.unit_price_usd,
                "total_price_usd": result.quote.total_price_usd,
                "discount_percent": result.quote.discount_percent,
                "inventory_sufficient": result.quote.inventory_sufficient,
                "status": quote_record.status if quote_record else "pending_selection",
            },
            "risk": {"requires_approval": risk_requires_approval, "reasons": risk.reasons},
            "email": {"subject": email.subject, "body": email.body, "status": email.status},
        }

    @app.get("/api/quotes")
    def quotes(request: Request, session: Session = Depends(session_dependency)) -> list[dict]:  # noqa: B008
        authorize_if_enabled(request, session)
        records = unique_quote_records(session.scalars(select(QuoteRecord).order_by(QuoteRecord.id.desc())).all())
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

    @app.get("/api/quotes/{quote_id}")
    def quote_detail(quote_id: int, request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session)
        record = session.scalar(select(QuoteRecord).where(QuoteRecord.id == quote_id).with_for_update())
        if record is None:
            raise HTTPException(status_code=404, detail="Quote not found")
        inquiry = parse_inquiry(record.inquiry_text)
        quote = QuoteDraft(
            customer_name=record.customer_name,
            sku=record.sku,
            quantity=record.quantity,
            unit_price_usd=record.unit_price_usd,
            total_price_usd=record.total_price_usd,
            discount_percent=record.discount_percent,
            inventory_sufficient=True,
            status=record.status,
        )
        risk = assess_quote_risk(quote)
        email = generate_email_draft(inquiry, quote)
        return {
            "id": record.id,
            "customer_name": record.customer_name,
            "inquiry_text": record.inquiry_text,
            "sku": record.sku,
            "quantity": record.quantity,
            "unit_price_usd": record.unit_price_usd,
            "total_price_usd": record.total_price_usd,
            "discount_percent": record.discount_percent,
            "status": record.status,
            "risk": {
                "requires_approval": record.status != "approved" and risk.requires_approval,
                "reasons": risk.reasons,
            },
            "email": {"subject": email.subject, "body": email.body, "status": email.status},
            "approval_history": [
                {
                    "id": item.id,
                    "from_status": item.from_status,
                    "to_status": item.to_status,
                    "actor": item.actor,
                    "created_at": item.created_at.isoformat(),
                }
                for item in session.scalars(
                    select(ApprovalHistory)
                    .where(ApprovalHistory.quote_id == record.id)
                    .order_by(ApprovalHistory.created_at.asc(), ApprovalHistory.id.asc())
                ).all()
            ],
            "inventory_movements": [
                {
                    "id": item.id,
                    "sku": item.sku,
                    "quantity": item.quantity,
                    "movement_type": item.movement_type,
                    "actor": item.actor,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                }
                for item in session.scalars(
                    select(InventoryMovement)
                    .where(InventoryMovement.quote_id == record.id)
                    .order_by(InventoryMovement.created_at.asc(), InventoryMovement.id.asc())
                ).all()
            ],
            "product_matches": rank_product_candidates(
                session,
                inquiry.product_keywords,
                inquiry.quantity,
                inquiry.project_type,
                keyword_weight=settings.product_keyword_weight,
                project_weight=settings.product_project_weight,
                quantity_weight=settings.product_quantity_weight,
            ),
        }

    @app.get("/api/customers")
    def customers(request: Request, q: Optional[str] = None, session: Session = Depends(session_dependency)) -> list[dict]:  # noqa: B008
        authorize_if_enabled(request, session)
        return [
            {"id": customer.id, "company_name": customer.company_name, "contact_name": customer.contact_name, "country": customer.country, "email": customer.email}
            for customer in search_customers(session, q)
        ]

    @app.post("/api/customers", status_code=201)
    def create_customer(payload: CustomerPayload, request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session, {"admin", "approver"})
        if not payload.company_name:
            raise HTTPException(status_code=422, detail="Company name is required")
        if lookup_customer(session, payload.company_name):
            raise HTTPException(status_code=409, detail="Customer already exists")
        customer = Customer(company_name=payload.company_name.strip(), contact_name=payload.contact_name or "", country=payload.country or "", email=payload.email or "")
        session.add(customer)
        session.commit()
        session.refresh(customer)
        return {"id": customer.id, "company_name": customer.company_name, "contact_name": customer.contact_name, "country": customer.country, "email": customer.email}

    @app.get("/api/customers/{customer_id}")
    def get_customer(customer_id: int, request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session)
        customer = session.get(Customer, customer_id)
        if customer is None:
            raise HTTPException(status_code=404, detail="Customer not found")
        return {"id": customer.id, "company_name": customer.company_name, "contact_name": customer.contact_name, "country": customer.country, "email": customer.email}

    @app.patch("/api/customers/{customer_id}")
    def update_customer(customer_id: int, payload: CustomerPayload, request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session, {"admin", "approver"})
        customer = session.get(Customer, customer_id)
        if customer is None:
            raise HTTPException(status_code=404, detail="Customer not found")
        for field in ("company_name", "contact_name", "country", "email"):
            value = getattr(payload, field)
            if value is not None:
                setattr(customer, field, value.strip())
        session.commit()
        session.refresh(customer)
        return {"id": customer.id, "company_name": customer.company_name, "contact_name": customer.contact_name, "country": customer.country, "email": customer.email}

    @app.delete("/api/customers/{customer_id}", status_code=204)
    def delete_customer(customer_id: int, request: Request, session: Session = Depends(session_dependency)) -> None:  # noqa: B008
        authorize_if_enabled(request, session, {"admin", "approver"})
        customer = session.get(Customer, customer_id)
        if customer is None:
            raise HTTPException(status_code=404, detail="Customer not found")
        session.delete(customer)
        session.commit()

    @app.get("/api/customers/{customer_id}/quotes")
    def customer_quotes(customer_id: int, request: Request, session: Session = Depends(session_dependency)) -> list[dict]:  # noqa: B008
        authorize_if_enabled(request, session)
        customer = session.get(Customer, customer_id)
        if customer is None:
            raise HTTPException(status_code=404, detail="Customer not found")
        records = unique_quote_records(session.scalars(select(QuoteRecord).where(QuoteRecord.customer_name == customer.company_name).order_by(QuoteRecord.id.desc())).all())
        return [{"id": record.id, "sku": record.sku, "quantity": record.quantity, "total_price_usd": record.total_price_usd, "status": record.status, "inquiry_text": record.inquiry_text} for record in records]

    @app.post("/api/quotes/{quote_id}/approve")
    def approve_quote_endpoint(quote_id: int, request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        user = authorize_if_enabled(request, session, {"admin", "approver"})
        actor = user.username if user else (request.headers.get("x-actor-id", "manual-review").strip()[:120] or "manual-review")
        record = session.scalar(select(QuoteRecord).where(QuoteRecord.id == quote_id).with_for_update())
        if record is None:
            raise HTTPException(status_code=404, detail="Quote not found")
        if record.status != "draft":
            raise HTTPException(status_code=409, detail="Only draft quotes can be approved")
        try:
            deduct_reserved_inventory(session, record.id, actor)
        except (LookupError, ValueError) as exc:
            session.rollback()
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        previous_status = record.status
        record.status = "approved"
        session.add(ApprovalHistory(
            quote_id=record.id,
            from_status=previous_status,
            to_status=record.status,
            actor=actor,
        ))
        agent_run = session.scalar(
            select(AgentRun)
            .where(AgentRun.inquiry_text == record.inquiry_text)
            .order_by(AgentRun.id.desc())
        )
        if agent_run is not None:
            agent_run.steps = [
                {**step, "status": "complete"}
                if step.get("name") == "Human approval"
                else step
                for step in agent_run.steps
            ]
        session.commit()
        return {"id": record.id, "status": record.status}

    @app.post("/api/quotes/{quote_id}/cancel")
    def cancel_quote_endpoint(quote_id: int, request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        user = authorize_if_enabled(request, session, {"admin", "approver"})
        actor = user.username if user else (request.headers.get("x-actor-id", "manual-review").strip()[:120] or "manual-review")
        record = session.get(QuoteRecord, quote_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Quote not found")
        if record.status != "draft":
            raise HTTPException(status_code=409, detail="Only draft quotes can be cancelled")
        try:
            release_reserved_inventory(session, record.id, actor)
        except ValueError as exc:
            session.rollback()
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        record.status = "cancelled"
        session.add(ApprovalHistory(quote_id=record.id, from_status="draft", to_status="cancelled", actor=actor))
        session.commit()
        return {"id": record.id, "status": record.status}

    @app.get("/api/agent-runs")
    def agent_runs(request: Request, session: Session = Depends(session_dependency)) -> list[dict]:  # noqa: B008
        authorize_if_enabled(request, session)
        records = session.scalars(select(AgentRun).order_by(AgentRun.id.desc())).all()
        return [
            {
                "run_id": record.run_id,
                "inquiry_text": record.inquiry_text,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "steps": record.steps,
            }
            for record in records
        ]

    @app.post("/api/rag/playground")
    def rag_playground(payload: RagPlaygroundRequest, request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        """Run an isolated RAG experiment without quotes, inventory, or agent-run writes."""
        authorize_if_enabled(request, session)
        started_at = time.perf_counter()

        parse_started_at = time.perf_counter()
        parsed = parse_inquiry(payload.inquiry)
        parse_ms = round((time.perf_counter() - parse_started_at) * 1000, 2)

        semantic_matches: dict[str, float] | None = None
        retrieval_mode = "rules"
        retrieval_started_at = time.perf_counter()
        if payload.mode == "semantic":
            if vector_store is None:
                raise HTTPException(status_code=409, detail="Semantic search is not enabled")
            try:
                semantic_matches = vector_store.search(
                    payload.inquiry,
                    limit=max(payload.top_k, 10) if reranker.enabled else payload.top_k,
                    min_score=payload.score_threshold,
                )
                retrieval_mode = "semantic" if semantic_matches else "semantic_empty"
            except (OSError, TimeoutError, ValueError, KeyError, ImportError, RuntimeError, json.JSONDecodeError) as exc:
                logger.exception("RAG playground semantic search failed; using rule matching")
                retrieval_mode = "rules_fallback"
                semantic_matches = None
                retrieval_error = str(exc)
            else:
                retrieval_error = None
        else:
            retrieval_error = None
        retrieval_ms = round((time.perf_counter() - retrieval_started_at) * 1000, 2)

        ranking_started_at = time.perf_counter()
        candidate_limit = max(payload.top_k, 10) if reranker.enabled else payload.top_k
        candidates = rank_product_candidates(
            session,
            parsed.product_keywords,
            parsed.quantity,
            parsed.project_type,
            budget_usd=parsed.budget_usd,
            max_lead_time_days=parsed.max_lead_time_days,
            limit=candidate_limit,
            keyword_weight=settings.product_keyword_weight,
            project_weight=settings.product_project_weight,
            quantity_weight=settings.product_quantity_weight,
            semantic_matches=semantic_matches,
        )
        attach_fallback_explanations(candidates)
        ranking_ms = round((time.perf_counter() - ranking_started_at) * 1000, 2)
        reranker_started_at = time.perf_counter()
        reranker_error = None
        reranker_scores: list[float] = []
        if reranker.enabled and candidates:
            try:
                products_by_sku = {
                    product.sku: product
                    for product in session.scalars(
                        select(Product).where(Product.sku.in_([candidate["sku"] for candidate in candidates]))
                    ).all()
                }
                documents = [
                    build_product_document(products_by_sku[candidate["sku"]]).text
                    for candidate in candidates
                    if candidate["sku"] in products_by_sku
                ]
                reranker_scores = reranker.score(payload.inquiry, documents)
                for candidate, reranker_score in zip(candidates, reranker_scores):
                    candidate["reranker_score"] = round(reranker_score, 4)
                    candidate["score"] = min(100, round(candidate["score"] * 0.6 + reranker_score * 40))
                    candidate["reasons"].append(f"Reranker match {reranker_score:.2f}")
                candidates.sort(key=lambda item: (-item["inventory_sufficient"], -item["score"], -(item.get("semantic_score") or 0), item["sku"]))
                candidates = candidates[:payload.top_k]
            except (ImportError, OSError, RuntimeError, TypeError, ValueError) as exc:
                reranker_error = str(exc)
                logger.exception("RAG reranker failed; using base ranking")
        reranker_ms = round((time.perf_counter() - reranker_started_at) * 1000, 2)
        best_score = candidates[0]["score"] if candidates else 0
        match_status = "reliable" if best_score >= 60 else "review" if best_score >= 45 else "no_reliable_match"

        result = {
            "mode": payload.mode,
            "retrieval_mode": retrieval_mode,
            "parsed": {
                "quantity": parsed.quantity,
                "destination_country": parsed.destination_country,
                "project_type": parsed.project_type,
                "product_keywords": parsed.product_keywords,
                "budget_usd": parsed.budget_usd,
                "max_lead_time_days": parsed.max_lead_time_days,
            },
            "timings": {
                "parse_ms": parse_ms,
                "retrieval_ms": retrieval_ms,
                "ranking_ms": ranking_ms,
                "reranker_ms": reranker_ms,
                "total_ms": round((time.perf_counter() - started_at) * 1000, 2),
            },
            "match_status": match_status,
            "match_threshold": 45,
            "reranker": {
                "enabled": reranker.enabled,
                "model": reranker.model_name if reranker.enabled else None,
                "scores_returned": len(reranker_scores),
                "error": reranker_error,
            },
            "candidates": candidates,
        }
        if retrieval_error:
            result["retrieval_error"] = retrieval_error
        return result

    @app.get("/api/evaluation")
    def evaluation(request: Request, session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session)
        dataset = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/evaluation/inquiries.json"))
        return evaluate_dataset(dataset)

    @app.get("/api/evaluation/rag")
    def rag_evaluation(request: Request, mode: str = Query(default="semantic", pattern="^(rules|semantic)$"), session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session)
        dataset = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/evaluation/rag_inquiries.json"))
        if mode == "semantic":
            if vector_store is None:
                raise HTTPException(status_code=409, detail="Semantic search is not enabled")
            try:
                return evaluate_rag_dataset(dataset, vector_store.search)
            except (OSError, TimeoutError, ValueError, KeyError, ImportError, RuntimeError, json.JSONDecodeError) as exc:
                raise HTTPException(status_code=503, detail="Semantic evaluation unavailable") from exc
        return evaluate_rag_dataset(dataset)

    @app.post("/api/evaluation/rag/run")
    def run_rag_evaluation(request: Request, mode: str = Query(default="semantic", pattern="^(rules|semantic)$"), session: Session = Depends(session_dependency)) -> dict:  # noqa: B008
        authorize_if_enabled(request, session)
        dataset = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/evaluation/rag_inquiries.json"))
        if mode == "semantic":
            if vector_store is None:
                raise HTTPException(status_code=409, detail="Semantic search is not enabled")
            try:
                metrics = evaluate_rag_dataset(dataset, vector_store.search)
            except (OSError, TimeoutError, ValueError, KeyError, ImportError, RuntimeError, json.JSONDecodeError) as exc:
                raise HTTPException(status_code=503, detail="Semantic evaluation unavailable") from exc
        else:
            metrics = evaluate_rag_dataset(dataset)
        record = RagEvaluationRun(
            **metrics,
            embedding_provider=active_embedding_profile["provider"] if mode == "semantic" else "rules",
            embedding_model=active_embedding_profile["model"] if mode == "semantic" else "rules",
            retrieval_config={
                "semantic_search_enabled": settings.semantic_search_enabled,
                "semantic_search_timeout_seconds": settings.semantic_search_timeout_seconds,
                "qdrant_collection": settings.qdrant_collection if mode == "semantic" else None,
            },
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return {**metrics, "id": record.id, "created_at": record.created_at.isoformat() if record.created_at else None}

    @app.get("/api/evaluation/rag/history")
    def rag_evaluation_history(request: Request, limit: int = Query(default=20, ge=1, le=100), session: Session = Depends(session_dependency)) -> list[dict]:  # noqa: B008
        authorize_if_enabled(request, session)
        return [
            {
                "id": record.id,
                "mode": record.mode,
                "embedding_provider": record.embedding_provider,
                "embedding_model": record.embedding_model,
                "retrieval_config": record.retrieval_config,
                "cases": record.cases,
                "evaluated_cases": record.evaluated_cases,
                "top1_recall": record.top1_recall,
                "top3_recall": record.top3_recall,
                "mrr": record.mrr,
                "misses": record.misses,
                "created_at": record.created_at.isoformat() if record.created_at else None,
            }
            for record in session.scalars(select(RagEvaluationRun).order_by(RagEvaluationRun.created_at.desc(), RagEvaluationRun.id.desc()).limit(limit)).all()
        ]

    return app
