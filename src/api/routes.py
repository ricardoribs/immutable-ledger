from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Query, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import jwt
from jwt import PyJWTError
from io import BytesIO
import base64
import qrcode

from src.api.dependencies import get_db
from src.domain.ledger import schemas, services, models
from src.core import security
from src.api import deps
from src.domain.security import services as security_services
from src.domain.security import models as security_models
import secrets
from src.infra.cache import cache

router = APIRouter()

# ==========================================
# AUTHENTICATION & SECURITY
# ==========================================


@router.post("/auth/login", response_model=schemas.TokenResponse)
async def login_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    otp: str = Query(None, description="Codigo 2FA ou Backup Code"),
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    accept_language = request.headers.get("accept-language", "")
    try:
        allow = await cache.check_rate_limit_sliding_window(f"rl_login:{ip}", limit=5, window_seconds=60)
        if not allow:
            raise HTTPException(status_code=429, detail="Muitas tentativas. Aguarde 1 minuto.")
    except Exception:
        # Se Redis cair, nao derruba login em dev
        pass

    account = await services.LedgerService.authenticate_account(db, form_data.username, form_data.password)
    if not account:
        raise HTTPException(status_code=400, detail="Credenciais invalidas")

    user_owner = account.owner
    if user_owner.mfa_enabled:
        if not otp:
            raise HTTPException(status_code=401, detail="MFA_REQUIRED")

        is_valid = await services.LedgerService.validate_second_factor(db, user_owner.id, otp)
        if not is_valid:
            raise HTTPException(status_code=401, detail="Codigo MFA invalido")

    jti_value = secrets.token_urlsafe(16)
    access_token = security.create_access_token(
        subject=user_owner.id,
        account_id=account.id,
        expires_delta=timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims={"jti": jti_value},
    )
    refresh_token = security.create_refresh_token(subject=user_owner.id)

    ip_addr = request.client.host if request.client else "unknown"
    fingerprint = security_services.SecurityService.compute_device_fingerprint(
        user_agent=user_agent,
        accept_language=accept_language,
        client_ip=ip_addr,
    )
    device, is_new = await security_services.SecurityService.upsert_device(
        db, user_owner.id, user_agent, ip_addr, fingerprint
    )
    if is_new:
        await security_services.SecurityService.create_alert(
            db, user_owner.id, "NEW_DEVICE", f"ip={ip_addr}"
        )
    await security_services.SecurityService.create_session(
        db,
        user_owner.id,
        jti=jti_value,
        user_agent=user_agent,
        ip_address=ip_addr,
        device_fingerprint=fingerprint,
        expires_at=None,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


# ==========================================
# MFA SETUP
# ==========================================


@router.get("/auth/mfa/setup")
async def mfa_setup(current_account: models.Account = Depends(deps.get_current_account)):
    user = current_account.owner
    if user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA ja ativado")

    uri = services.LedgerService.get_mfa_uri(f"LuisBank:{user.email}", user.mfa_secret)
    return {"otp_uri": uri, "secret": user.mfa_secret}


@router.get("/auth/mfa/qrcode")
async def mfa_qrcode(current_account: models.Account = Depends(deps.get_current_account)):
    user = current_account.owner
    if user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA ja ativado")
    uri = services.LedgerService.get_mfa_uri(f"LuisBank:{user.email}", user.mfa_secret)
    img = qrcode.make(uri)
    buf = BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return {"qr_code_png_base64": encoded, "otp_uri": uri}


@router.post("/auth/mfa/enable")
async def mfa_enable(
    code: str = Query(...),
    current_account: models.Account = Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    backup_codes = await services.LedgerService.enable_mfa(db, current_account.id, code)
    return {"message": "MFA ativado!", "backup_codes": backup_codes}


@router.post("/auth/refresh", response_model=schemas.TokenResponse)
async def refresh_token(
    request: Request,
    data: schemas.RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    accept_language = request.headers.get("accept-language", "")
    try:
        payload = jwt.decode(data.refresh_token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Refresh token invalido")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token invalido")

    user_id = payload.get("sub")
    jti = payload.get("jti")
    exp = payload.get("exp")
    if not user_id or not jti or not exp:
        raise HTTPException(status_code=401, detail="Refresh token invalido")

    try:
        if await cache.is_jti_blacklisted(str(jti)):
            raise HTTPException(status_code=401, detail="Refresh token revogado")
    except Exception:
        pass

    fingerprint = security_services.SecurityService.compute_device_fingerprint(
        user_agent=user_agent,
        accept_language=accept_language,
        client_ip=ip,
    )
    stmt_dev = select(security_models.Device).where(
        security_models.Device.user_id == int(user_id),
        security_models.Device.fingerprint == fingerprint,
    )
    dev_res = await db.execute(stmt_dev)
    if not dev_res.scalar_one_or_none():
        raise HTTPException(status_code=401, detail="Dispositivo nao reconhecido")

    exp_dt = datetime.fromtimestamp(int(exp), tz=timezone.utc)
    ttl_seconds = max(0, int((exp_dt - datetime.now(timezone.utc)).total_seconds()))
    try:
        await cache.add_jti_to_blacklist(str(jti), expire_in_seconds=ttl_seconds)
    except Exception:
        pass

    stmt_acc = select(models.Account).where(models.Account.user_id == int(user_id))
    res_acc = await db.execute(stmt_acc)
    account = res_acc.scalars().first()
    if not account:
        raise HTTPException(status_code=401, detail="Conta nao encontrada")

    new_jti = secrets.token_urlsafe(16)
    access_token = security.create_access_token(
        subject=user_id,
        account_id=account.id,
        expires_delta=timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims={"jti": new_jti},
    )
    new_refresh = security.create_refresh_token(subject=user_id)

    await security_services.SecurityService.create_session(
        db,
        int(user_id),
        jti=new_jti,
        user_agent=user_agent,
        ip_address=ip,
        device_fingerprint=fingerprint,
        expires_at=None,
    )

    return {
        "access_token": access_token,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


@router.post("/auth/logout")
async def logout(
    request: Request,
    refresh_token: str | None = Query(None),
):
    auth = request.headers.get("Authorization") or ""
    if auth.startswith("Bearer "):
        access_token = auth.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(access_token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                exp_dt = datetime.fromtimestamp(int(exp), tz=timezone.utc)
                ttl_seconds = max(0, int((exp_dt - datetime.now(timezone.utc)).total_seconds()))
                await cache.add_jti_to_blacklist(str(jti), expire_in_seconds=ttl_seconds)
        except Exception:
            pass

    if refresh_token:
        try:
            payload = jwt.decode(refresh_token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                exp_dt = datetime.fromtimestamp(int(exp), tz=timezone.utc)
                ttl_seconds = max(0, int((exp_dt - datetime.now(timezone.utc)).total_seconds()))
                await cache.add_jti_to_blacklist(str(jti), expire_in_seconds=ttl_seconds)
        except Exception:
            pass

    return {"status": "ok"}


# ==========================================
# GESTAO DE CONTAS
# ==========================================


@router.get("/accounts/me", response_model=schemas.AccountResponse)
async def read_users_me(
    current_account: models.Account = Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(models.Account).options(
        selectinload(models.Account.owner),
        selectinload(models.Account.pix_keys),
    ).where(models.Account.id == current_account.id)

    result = await db.execute(stmt)
    account_full = result.scalar_one()

    cpf_last4 = account_full.owner.cpf_last4 or ""
    cpf_masked = f"***.***.{cpf_last4}" if cpf_last4 else "***"
    balance = await services.LedgerService.get_balance(db, account_full.id)

    pix_keys_data = []
    if account_full.pix_keys:
        pix_keys_data = [schemas.PixKeyResponse.model_validate(k) for k in account_full.pix_keys]

    return {
        "id": account_full.id,
        "account_number": account_full.account_number,
        "balance": balance,
        "name": account_full.owner.name,
        "cpf_masked": cpf_masked,
        "mfa_enabled": account_full.owner.mfa_enabled,
        "pix_keys": pix_keys_data,
        "account_type": account_full.account_type,
        "blocked_balance": account_full.blocked_balance,
        "overdraft_limit": account_full.overdraft_limit,
    }


@router.post("/accounts", response_model=schemas.AccountResponse, status_code=201)
async def create_account(data: schemas.AccountCreate, db: AsyncSession = Depends(get_db)):
    new_account = await services.LedgerService.create_account(db, data)
    cpf_last4 = new_account.owner.cpf_last4 or ""
    cpf_masked = f"***.***.{cpf_last4}" if cpf_last4 else "***"
    pix_keys_data = []
    if new_account.pix_keys:
        pix_keys_data = [schemas.PixKeyResponse.model_validate(k) for k in new_account.pix_keys]
    return {
        "id": new_account.id,
        "account_number": new_account.account_number,
        "balance": new_account.balance,
        "name": new_account.owner.name,
        "cpf_masked": cpf_masked,
        "mfa_enabled": new_account.owner.mfa_enabled,
        "pix_keys": pix_keys_data,
        "account_type": new_account.account_type,
        "blocked_balance": new_account.blocked_balance,
        "overdraft_limit": new_account.overdraft_limit,
    }


@router.get("/accounts", response_model=list[schemas.AccountResponse])
async def list_accounts(
    current_account: models.Account = Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    accounts = await services.LedgerService.list_accounts(db, current_account.owner.id)
    response = []
    for acc in accounts:
        cpf_last4 = acc.owner.cpf_last4 or ""
        cpf_masked = f"***.***.{cpf_last4}" if cpf_last4 else "***"
        pix_keys_data = []
        if acc.pix_keys:
            pix_keys_data = [schemas.PixKeyResponse.model_validate(k) for k in acc.pix_keys]
        balance = await services.LedgerService.get_balance(db, acc.id)
        response.append({
            "id": acc.id,
            "account_number": acc.account_number,
            "balance": balance,
            "name": acc.owner.name,
            "cpf_masked": cpf_masked,
            "mfa_enabled": acc.owner.mfa_enabled,
            "pix_keys": pix_keys_data,
            "account_type": acc.account_type,
            "blocked_balance": acc.blocked_balance,
            "overdraft_limit": acc.overdraft_limit,
        })
    return response


@router.get("/accounts/consolidated")
async def consolidated_balance(
    current_account: models.Account = Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    accounts = await services.LedgerService.list_accounts(db, current_account.owner.id)
    balances = [await services.LedgerService.get_balance(db, acc.id) for acc in accounts]
    total = sum(balances)
    return {"total_balance": total, "accounts": len(accounts)}


# ==========================================
# CORE BANKING
# ==========================================


@router.get("/accounts/{account_id}/balance")
async def get_balance(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_account: models.Account = Depends(deps.get_current_account),
):
    if account_id != current_account.id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    balance = await services.LedgerService.get_balance(db, account_id)
    return {"account_id": account_id, "balance": balance}


@router.get("/accounts/{account_id}/statement")
async def get_statement(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_account: models.Account = Depends(deps.get_current_account),
    start_date: str | None = None,
    end_date: str | None = None,
    tx_type: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    search: str | None = None,
):
    if account_id != current_account.id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    return await services.LedgerService.get_statement(
        db,
        account_id,
        start_date=start_date,
        end_date=end_date,
        tx_type=tx_type,
        min_amount=min_amount,
        max_amount=max_amount,
        search=search,
    )


@router.get("/accounts/{account_id}/statement/export")
async def export_statement(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_account: models.Account = Depends(deps.get_current_account),
):
    if account_id != current_account.id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    data = await services.LedgerService.get_statement(db, account_id)
    rows = ["date,amount,type,description"]
    for tx in data["transactions"]:
        rows.append(f"{tx['date']},{tx['amount']},{tx['type']},{tx['description']}")
    csv = "\n".join(rows)
    return Response(content=csv, media_type="text/csv")


@router.post("/transactions", status_code=201, response_model=schemas.TransactionResponse)
async def create_transaction(
    request: Request,
    data: schemas.TransactionCreate,
    response: Response,
    otp: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_account: models.Account = Depends(deps.get_current_account),
):
    if data.account_id != current_account.id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    accept_language = request.headers.get("accept-language", "")
    fingerprint = security_services.SecurityService.compute_device_fingerprint(
        user_agent=user_agent,
        accept_language=accept_language,
        client_ip=ip,
    )
    fraud_context = {
        "ip": ip,
        "user_agent": user_agent,
        "device_fingerprint": fingerprint,
    }
    tx = await services.LedgerService.create_transaction(db, data, otp, fraud_context=fraud_context)
    if getattr(tx, "idempotency_hit", False):
        response.headers["x-idempotency-hit"] = "true"
    return tx


@router.get("/transactions/{transaction_id}/receipt")
async def transaction_receipt(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_account: models.Account = Depends(deps.get_current_account),
):
    tx = await services.LedgerService.get_transaction_by_id(db, transaction_id)
    if not tx or tx.account_id != current_account.id:
        raise HTTPException(status_code=404, detail="Transacao nao encontrada")
    return {
        "id": tx.id,
        "account_id": tx.account_id,
        "amount": tx.amount,
        "type": tx.operation_type,
        "description": tx.description,
        "timestamp": str(tx.timestamp),
    }


@router.post("/transfers", status_code=201, response_model=schemas.TransactionResponse)
async def create_transfer(
    request: Request,
    data: schemas.TransferCreate,
    response: Response,
    otp: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_account: models.Account = Depends(deps.get_current_account),
):
    if data.from_account_id != current_account.id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    accept_language = request.headers.get("accept-language", "")
    fingerprint = security_services.SecurityService.compute_device_fingerprint(
        user_agent=user_agent,
        accept_language=accept_language,
        client_ip=ip,
    )
    fraud_context = {
        "ip": ip,
        "user_agent": user_agent,
        "device_fingerprint": fingerprint,
    }
    tx = await services.LedgerService.process_transfer(db, data, otp, fraud_context=fraud_context)
    if getattr(tx, "idempotency_hit", False):
        response.headers["x-idempotency-hit"] = "true"
    return tx


@router.get("/ledger/integrity")
async def ledger_integrity(
    current_account: models.Account = Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.LedgerService.verify_integrity(db)


# ==========================================
# MODULO PIX
# ==========================================


@router.post("/pix/keys", status_code=201, response_model=schemas.PixKeyResponse)
async def create_pix_key(
    data: schemas.PixKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_account: models.Account = Depends(deps.get_current_account),
):
    return await services.LedgerService.create_pix_key(db, current_account.id, data)


@router.post("/pix/transfer", status_code=201, response_model=schemas.TransactionResponse)
async def pix_transfer(
    request: Request,
    data: schemas.PixTransferCreate,
    response: Response,
    otp: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_account: models.Account = Depends(deps.get_current_account),
):
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    accept_language = request.headers.get("accept-language", "")
    fingerprint = security_services.SecurityService.compute_device_fingerprint(
        user_agent=user_agent,
        accept_language=accept_language,
        client_ip=ip,
    )
    fraud_context = {
        "ip": ip,
        "user_agent": user_agent,
        "device_fingerprint": fingerprint,
    }
    tx = await services.LedgerService.process_pix_transfer(
        db, data, current_account.id, otp, fraud_context=fraud_context
    )
    if getattr(tx, "idempotency_hit", False):
        response.headers["x-idempotency-hit"] = "true"
    return tx
