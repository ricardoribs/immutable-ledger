import pytest
import httpx
from uuid import uuid4

# URL da API rodando no Docker
BASE_URL = "http://localhost:8000"

# ==========================================
# UTILITÁRIOS
# ==========================================
def get_random_name():
    return f"Tester_{uuid4().hex[:8]}"

def get_idem_key():
    return str(uuid4())

# ==========================================
# TESTES
# ==========================================

@pytest.mark.asyncio
async def test_health_check():
    """Verifica se a API está viva"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_create_account_and_login():
    """Testa criação de conta e login com senha"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. Cria Conta (AGORA COM SENHA)
        name = get_random_name()
        password = "secret_password"
        
        # CORREÇÃO: Adicionamos o campo "password"
        resp_create = await client.post("/ledger/accounts", json={"name": name, "password": password})
        
        assert resp_create.status_code == 201
        data = resp_create.json()
        account_id = data["id"]
        assert "id" in data
        
        # 2. Tenta Logar (Sucesso)
        resp_login = await client.post("/ledger/login", json={"account_id": account_id, "password": password})
        assert resp_login.status_code == 200
        
        # 3. Tenta Logar (Senha Errada)
        resp_fail = await client.post("/ledger/login", json={"account_id": account_id, "password": "wrong"})
        assert resp_fail.status_code == 401

@pytest.mark.asyncio
async def test_deposit_and_idempotency():
    """Testa depósito e se o sistema bloqueia duplicação (Idempotência)"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Cria conta (AGORA COM SENHA)
        resp = await client.post("/ledger/accounts", json={"name": "Idem Test", "password": "123"})
        acc_id = resp.json()["id"]
        
        # Prepara Depósito
        idem_key = get_idem_key() # Chave ÚNICA
        amount = 5000 # R$ 50,00
        payload = {
            "idempotency_key": idem_key,
            "amount": amount,
            "type": "DEPOSIT",
            "account_id": acc_id
        }
        
        # 1. Primeiro Envio (Deve funcionar)
        resp_1 = await client.post("/ledger/transactions", json=payload)
        assert resp_1.status_code == 201
        
        # 2. Segundo Envio com MESMA chave (Deve ser bloqueado pelo Redis)
        resp_2 = await client.post("/ledger/transactions", json=payload)
        assert resp_2.status_code == 409 # Conflict (Erro esperado)
        assert "duplicada" in resp_2.json()["detail"]
        
        # 3. Verifica Saldo (Deve ter entrado apenas 50, não 100)
        resp_bal = await client.get(f"/ledger/accounts/{acc_id}/balance")
        assert resp_bal.json()["balance"] == 5000

@pytest.mark.asyncio
async def test_transfer_flow():
    """Cria duas contas e transfere dinheiro entre elas"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Cria Conta A (AGORA COM SENHA)
        r1 = await client.post("/ledger/accounts", json={"name": "User A", "password": "123"})
        id_a = r1.json()["id"]
        
        # Cria Conta B (AGORA COM SENHA)
        r2 = await client.post("/ledger/accounts", json={"name": "User B", "password": "123"})
        id_b = r2.json()["id"]
        
        # Deposita 1000 na Conta A
        await client.post("/ledger/transactions", json={
            "idempotency_key": get_idem_key(),
            "amount": 1000,
            "type": "DEPOSIT",
            "account_id": id_a
        })
        
        # Transfere 400 de A para B
        resp_transfer = await client.post("/ledger/transfers", json={
            "idempotency_key": get_idem_key(),
            "amount": 400,
            "from_account_id": id_a,
            "to_account_id": id_b
        })
        assert resp_transfer.status_code == 201
        
        # Verifica Saldos Finais
        bal_a = await client.get(f"/ledger/accounts/{id_a}/balance")
        assert bal_a.json()["balance"] == 600
        
        bal_b = await client.get(f"/ledger/accounts/{id_b}/balance")
        assert bal_b.json()["balance"] == 400

@pytest.mark.asyncio
async def test_insufficient_funds():
    """Tenta sacar mais do que tem"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Cria conta (AGORA COM SENHA)
        resp = await client.post("/ledger/accounts", json={"name": "Broke Guy", "password": "123"})
        acc_id = resp.json()["id"]
        
        # Tenta sacar 100 (Saldo é 0)
        payload = {
            "idempotency_key": get_idem_key(),
            "amount": 100,
            "type": "WITHDRAW",
            "account_id": acc_id
        }
        resp_w = await client.post("/ledger/transactions", json=payload)
        
        assert resp_w.status_code == 422 # Unprocessable Entity
        assert "Insufficient funds" in resp_w.json()["detail"]