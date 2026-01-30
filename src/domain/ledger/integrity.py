import time
from src.infra.database import async_session
from src.infra.metrics import LEDGER_INTEGRITY_OK, LEDGER_INTEGRITY_LAST_RUN, LEDGER_INTEGRITY_FAILURES
from src.infra.alerting import send_alert
from src.domain.ledger import services as ledger_services


async def run_integrity_check() -> dict:
    try:
        async with async_session() as db:
            result = await ledger_services.LedgerService.verify_integrity(db)
        LEDGER_INTEGRITY_LAST_RUN.set(time.time())
        if not result.get("ok"):
            LEDGER_INTEGRITY_OK.set(0)
            LEDGER_INTEGRITY_FAILURES.inc()
            await send_alert(
                event="LEDGER_INTEGRITY_FAILURE",
                severity="critical",
                details=f"tx_id={result.get('tx_id')} reason={result.get('reason')}",
            )
            return result
        LEDGER_INTEGRITY_OK.set(1)
        return result
    except Exception as exc:
        LEDGER_INTEGRITY_LAST_RUN.set(time.time())
        LEDGER_INTEGRITY_OK.set(0)
        LEDGER_INTEGRITY_FAILURES.inc()
        await send_alert(
            event="LEDGER_INTEGRITY_ERROR",
            severity="critical",
            details=str(exc),
        )
        return {"ok": False, "reason": "INTEGRITY_ERROR"}
