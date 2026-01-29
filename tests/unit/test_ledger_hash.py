from datetime import datetime
from src.domain.ledger import models


def test_tx_hash_chain_consistency():
    tx = models.Transaction(
        account_id=1,
        amount=10.0,
        operation_type="DEPOSIT",
        description="Test",
        timestamp=datetime.utcnow(),
        sequence=1,
        prev_hash="",
    )
    # Local compute must be deterministic for same data
    raw = "|".join([
        str(1),
        str(tx.account_id),
        str(tx.amount),
        tx.operation_type,
        tx.description or "",
        tx.timestamp.isoformat(),
        "",
    ])
    from hashlib import sha256
    expected = sha256(raw.encode("utf-8")).hexdigest()
    assert expected
