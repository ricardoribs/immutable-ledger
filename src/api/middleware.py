from starlette.middleware.base import BaseHTTPMiddleware
from starlette.concurrency import run_in_threadpool
from fastapi import Request
from fastapi.responses import JSONResponse
from jose import jwt as jose_jwt

from src.infra.cache import cache
from src.infra.database import SessionLocal
from src.domain.ledger.models import AuditLog
from src.infra.metrics import REQUEST_LATENCY, ERRORS

import logging
import time
import hashlib
from datetime import datetime
from sqlalchemy import select

logger = logging.getLogger(__name__)


class LedgerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        xff = request.headers.get("x-forwarded-for", "")
        ip = (xff.split(",")[0].strip() if xff else None) or (request.client.host if request.client else "unknown")

        path = request.url.path
        method = request.method.upper()

        # ==========================
        # 1) GLOBAL RATE LIMIT
        # ==========================
        exclude_rl = {"/metrics", "/health", "/docs", "/openapi.json"}
        if method != "OPTIONS" and path not in exclude_rl:
            try:
                allow = await cache.check_rate_limit_sliding_window(f"global:{ip}", limit=100, window_seconds=60)
                if not allow:
                    logger.warning(f"Rate limit excedido ip={ip} path={path}")
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Global Rate Limit Exceeded. Acalme-se, hacker."},
                    )
            except Exception as e:
                # Se Redis cair, nao derruba a API
                logger.error(f"Rate limit indisponivel (redis): {e}")

        # ==========================
        # 2) REQUEST
        # ==========================
        start = time.time()
        try:
            response = await call_next(request)
        except Exception as e:
            logger.exception(f"Erro nao tratado: {e}")
            response = JSONResponse(status_code=500, content={"detail": "Erro interno"})
        process_time = time.time() - start
        REQUEST_LATENCY.labels(path=path, method=method, status=str(response.status_code)).observe(process_time)
        if response.status_code >= 400:
            ERRORS.labels(path=path, method=method, status=str(response.status_code)).inc()

        # ==========================
        # 3) AUDIT LOG
        # ==========================
        exclude_audit = {"/metrics", "/health", "/docs", "/openapi.json"}
        if path not in exclude_audit:
            await run_in_threadpool(self._save_audit_log_sync, request, response.status_code, ip, process_time)

        return response

    def _save_audit_log_sync(self, request: Request, status_code: int, ip: str, process_time: float):
        user_id = None
        user_agent = request.headers.get("user-agent", "")
        auth = request.headers.get("Authorization") or ""
        if auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1].strip()
            try:
                claims = jose_jwt.get_unverified_claims(token)
                sub = claims.get("sub")
                if sub and str(sub).isdigit():
                    user_id = int(sub)
            except Exception:
                user_id = None

        details = f"status={status_code} duration_ms={int(process_time * 1000)}"
        timestamp = datetime.utcnow()

        try:
            with SessionLocal() as db:
                stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(1)
                last_log = db.execute(stmt).scalar_one_or_none()
                prev_hash = last_log.record_hash if last_log else ""
                base = "|".join([
                    f"HTTP {request.method}",
                    str(user_id or ""),
                    ip,
                    request.method,
                    request.url.path,
                    details,
                    timestamp.isoformat(),
                    prev_hash or "",
                ])
                record_hash = hashlib.sha256(base.encode("utf-8")).hexdigest()

                log = AuditLog(
                    action=f"HTTP {request.method}",
                    user_id=user_id,
                    ip_address=ip,
                    method=request.method,
                    path=request.url.path,
                    details=details,
                    user_agent=user_agent,
                    prev_hash=prev_hash,
                    record_hash=record_hash,
                    timestamp=timestamp,
                )
                db.add(log)
                db.commit()
        except Exception as e:
            logger.error(f"Falha ao salvar Audit Log: {e}")
