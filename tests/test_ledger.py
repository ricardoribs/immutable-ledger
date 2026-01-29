import secrets
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_full_ledger_scenario(client: AsyncClient):
    suffix = secrets.token_hex(4)
    cpf_suffix = f"{secrets.randbelow(1000):03d}"
    payload_account = {
        "name": "Integration User",
        "cpf": f"12345678{cpf_suffix}",
        "email": f"integration-{suffix}@example.com",
        "password": "SenhaForte123",
        "account_type": "CHECKING",
    }
    resp_acc = await client.post("/ledger/accounts", json=payload_account)

    assert resp_acc.status_code == 201
    account_data = resp_acc.json()
    account_id = account_data["id"]

    resp_login = await client.post(
        "/ledger/auth/login",
        data={"username": payload_account["email"], "password": payload_account["password"]},
    )
    assert resp_login.status_code == 200
    token = resp_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload_deposit = {
        "idempotency_key": f"test-e2e-deposit-{suffix}",
        "amount": 10.0,
        "type": "DEPOSIT",
        "account_id": account_id,
    }
    resp_dep = await client.post("/ledger/transactions", json=payload_deposit, headers=headers)
    assert resp_dep.status_code == 201
    assert resp_dep.json()["amount"] == 10.0

    resp_bal = await client.get(f"/ledger/accounts/{account_id}/balance", headers=headers)
    assert resp_bal.status_code == 200
    assert resp_bal.json()["balance"] == 10.0

    resp_idem = await client.post("/ledger/transactions", json=payload_deposit, headers=headers)
    assert resp_idem.status_code == 201
    assert resp_idem.headers.get("x-idempotency-hit") == "true"

    payload_withdraw = {
        "idempotency_key": f"test-e2e-withdraw-fail-{suffix}",
        "amount": 1000000,
        "type": "WITHDRAW",
        "account_id": account_id,
    }
    resp_fail = await client.post("/ledger/transactions", json=payload_withdraw, headers=headers)
    assert resp_fail.status_code == 403
    assert "KYC_REQUIRED" in resp_fail.json()["detail"]
