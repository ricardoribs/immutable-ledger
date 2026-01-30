from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
try:
    from prometheus_fastapi_instrumentator import Instrumentator
except Exception:
    Instrumentator = None
from src.api import routes
from src.api import security_routes
from src.api import payments_routes
from src.api import pix_routes
from src.api import cards_routes
from src.api import loans_routes
from src.api import investments_routes
from src.api import insurance_routes
from src.api import billing_routes
from src.api import pj_routes
from src.api import open_banking_routes
from src.api import support_routes
from src.api import settings_routes
from src.api import utilities_routes
from src.api import compliance_routes
from src.api import fraud_routes
from src.api import notifications_routes
from src.api import regulatory_routes
from src.api import ml_routes
from src.api import feature_flags_routes
from src.infra.database import init_db
from src.infra.cache import cache
from src.api.middleware import LedgerMiddleware
from src.infra.logging import configure_logging
from src.infra.metrics import TOTAL_BALANCE
from src.infra.database import async_session
from sqlalchemy import select, func
from src.domain.ledger import models as ledger_models
from src.domain.ledger.integrity import run_integrity_check
from src.core.config import settings
import asyncio

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
except Exception:
    FastAPIInstrumentor = None
    trace = None
    TracerProvider = None
    BatchSpanProcessor = None
    OTLPSpanExporter = None
    Resource = None
import os
app = FastAPI(title="LuisBank Ledger API", version="1.0.0")

configure_logging()

if FastAPIInstrumentor and TracerProvider and Resource:
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317")
    service_name = os.getenv("OTEL_SERVICE_NAME", "ledger-api")
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    trace.set_tracer_provider(provider)
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
    provider.add_span_processor(processor)
    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)

# MIDDLEWARES (ordem: ultimo adicionado roda primeiro)
app.add_middleware(LedgerMiddleware)

# Em dev, deixa permissivo sem credenciais (evita conflito com "*" + credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    print("Inicializando API LuisBank...")
    await init_db()
    try:
        await cache.get_value("health_check")
        print("Redis conectado.")
    except Exception as e:
        print(f"Falha no Redis: {e}")

    async def update_total_balance():
        while True:
            async with async_session() as db:
                stmt = select(func.coalesce(func.sum(ledger_models.Account.balance), 0.0))
                res = await db.execute(stmt)
                TOTAL_BALANCE.set(float(res.scalar() or 0.0))
            await asyncio.sleep(30)

    asyncio.create_task(update_total_balance())

    async def ledger_integrity_loop():
        while True:
            await run_integrity_check()
            await asyncio.sleep(settings.LEDGER_INTEGRITY_INTERVAL_SECONDS)

    if not os.getenv("PYTEST_CURRENT_TEST"):
        asyncio.create_task(ledger_integrity_loop())


@app.on_event("shutdown")
async def shutdown_event():
    await cache.close()


app.include_router(routes.router, prefix="/ledger", tags=["Ledger"])
app.include_router(security_routes.router)
app.include_router(payments_routes.router)
app.include_router(pix_routes.router)
app.include_router(cards_routes.router)
app.include_router(loans_routes.router)
app.include_router(investments_routes.router)
app.include_router(insurance_routes.router)
app.include_router(billing_routes.router)
app.include_router(pj_routes.router)
app.include_router(open_banking_routes.router)
app.include_router(support_routes.router)
app.include_router(settings_routes.router)
app.include_router(utilities_routes.router)
app.include_router(compliance_routes.router)
app.include_router(fraud_routes.router)
app.include_router(notifications_routes.router)
app.include_router(regulatory_routes.router)
app.include_router(ml_routes.router)
app.include_router(feature_flags_routes.router)


@app.get("/health")
async def health_check():
    db_ok = True
    cache_ok = True
    try:
        async with async_session() as db:
            await db.execute(select(1))
    except Exception:
        db_ok = False
    try:
        await cache.get_value("health_check")
    except Exception:
        cache_ok = False
    status = "ok" if db_ok and cache_ok else "degraded"
    return {"status": status, "db": db_ok, "cache": cache_ok}


if Instrumentator:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
