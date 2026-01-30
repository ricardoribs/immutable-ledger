from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from datetime import timedelta, datetime

from src.domain.ledger import models, schemas
from src.infra.cache import cache
from src.core import security
from src.core.config import settings
from src.infra.metrics import TRANSACTION_COUNT
from src.core.encryption import CryptoService
from src.domain.security.tokenization import TokenizationService
from src.domain.regulatory import models as regulatory_models
from src.domain.settings import models as settings_models
from src.core.money import to_decimal

import pyotp
import random
import secrets
import hashlib

# Threshold em unidades (R$). Converta cents -> unidades antes de validar.
MFA_THRESHOLD_UNITS = to_decimal("1000.00")


class LedgerService:
    @staticmethod
    def _ensure_account_active(account: models.Account):
        if not account:
            raise HTTPException(status_code=404, detail="Conta nao encontrada")
        if account.status != "ACTIVE":
            raise HTTPException(status_code=403, detail="Conta inativa ou bloqueada")

    @staticmethod
    async def _get_account_for_update(db: AsyncSession, account_id: int) -> models.Account | None:
        stmt = select(models.Account).where(models.Account.id == account_id).with_for_update()
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def _get_accounts_for_update(db: AsyncSession, account_ids: list[int]) -> dict[int, models.Account]:
        if not account_ids:
            return {}
        stmt = (
            select(models.Account)
            .where(models.Account.id.in_(account_ids))
            .order_by(models.Account.id.asc())
            .with_for_update()
        )
        res = await db.execute(stmt)
        return {acc.id: acc for acc in res.scalars().all()}

    @staticmethod
    async def _ensure_kyc_for_outbound(db: AsyncSession, user_id: int, amount_units: float):
        if amount_units < to_decimal(settings.KYC_REQUIRED_THRESHOLD):
            return
        stmt = select(regulatory_models.KycProfile).where(regulatory_models.KycProfile.user_id == user_id)
        res = await db.execute(stmt)
        profile = res.scalar_one_or_none()
        if not profile or profile.status != "VERIFIED":
            raise HTTPException(status_code=403, detail="KYC_REQUIRED")

    @staticmethod
    async def _get_user_limits(db: AsyncSession, user_id: int) -> settings_models.LimitConfig:
        stmt = select(settings_models.LimitConfig).where(settings_models.LimitConfig.user_id == user_id)
        res = await db.execute(stmt)
        cfg = res.scalar_one_or_none()
        if not cfg:
            cfg = settings_models.LimitConfig(user_id=user_id)
            db.add(cfg)
            await db.commit()
        return cfg

    @staticmethod
    async def _get_system_account(db: AsyncSession, for_update: bool = False) -> models.Account:
        stmt_user = select(models.User).where(models.User.email == settings.SYSTEM_USER_EMAIL)
        res_user = await db.execute(stmt_user)
        sys_user = res_user.scalar_one_or_none()
        if not sys_user:
            sys_user = models.User(
                name="System",
                cpf="",
                cpf_hash=f"system_{settings.SYSTEM_USER_EMAIL}",
                cpf_token=None,
                cpf_last4=None,
                email=settings.SYSTEM_USER_EMAIL,
                hashed_password=security.get_password_hash(secrets.token_urlsafe(16)),
                mfa_secret="",
                mfa_enabled=False,
            )
            db.add(sys_user)
            await db.flush()

        stmt_acc = select(models.Account).where(models.Account.account_number == settings.SYSTEM_ACCOUNT_NUMBER)
        if for_update:
            stmt_acc = stmt_acc.with_for_update()
        res_acc = await db.execute(stmt_acc)
        sys_acc = res_acc.scalar_one_or_none()
        if not sys_acc:
            sys_acc = models.Account(
                account_number=settings.SYSTEM_ACCOUNT_NUMBER,
                balance=to_decimal("0.00"),
                blocked_balance=to_decimal("0.00"),
                overdraft_limit=to_decimal("0.00"),
                account_type="TREASURY",
                user_id=sys_user.id,
                owner=sys_user,
            )
            db.add(sys_acc)
            await db.flush()
        return sys_acc

    @staticmethod
    def _ensure_double_entry(postings: list[models.Posting]) -> None:
        total = to_decimal("0.00")
        for posting in postings:
            total = to_decimal(total + to_decimal(posting.amount))
        if total != to_decimal("0.00"):
            raise HTTPException(status_code=500, detail="Invariancia double-entry violada")

    @staticmethod
    async def _compute_tx_hash(
        db: AsyncSession,
        tx: models.Transaction,
    ) -> tuple[int, str]:
        stmt_update = (
            update(models.LedgerSequence)
            .where(models.LedgerSequence.id == 1)
            .values(value=models.LedgerSequence.value + 1)
            .returning(models.LedgerSequence.value)
        )
        res_update = await db.execute(stmt_update)
        seq_value = res_update.scalar_one_or_none()
        if seq_value is None:
            seq_row = models.LedgerSequence(id=1, value=1)
            db.add(seq_row)
            await db.flush()
            sequence = 1
        else:
            sequence = int(seq_value)

        stmt_prev = select(models.Transaction).where(models.Transaction.sequence == sequence - 1)
        res_prev = await db.execute(stmt_prev)
        last_tx = res_prev.scalar_one_or_none()
        prev_hash = last_tx.record_hash if last_tx else ""
        raw = "|".join([
            str(sequence),
            str(tx.account_id),
            str(tx.amount),
            tx.operation_type,
            tx.description or "",
            tx.timestamp.isoformat(),
            prev_hash or "",
        ])
        record_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return sequence, prev_hash, record_hash

    @staticmethod
    async def create_account(db: AsyncSession, data: schemas.AccountCreate):
        result = await db.execute(select(models.User).filter(models.User.email == data.email))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Email ja cadastrado.")
        cpf_hash = hashlib.sha256(data.cpf.encode()).hexdigest()
        result_cpf = await db.execute(select(models.User).filter(models.User.cpf_hash == cpf_hash))
        if result_cpf.scalars().first():
            raise HTTPException(status_code=400, detail="CPF ja cadastrado.")

        hashed_pwd = security.get_password_hash(data.password)
        secret = pyotp.random_base32()
        cpf_hash = hashlib.sha256(data.cpf.encode()).hexdigest()
        cpf_last4 = data.cpf[-4:] if data.cpf else ""
        cpf_token = await TokenizationService.tokenize(
            db, data.cpf, token_type="CPF", user_id=None, last4=cpf_last4
        )
        try:
            db_user = models.User(
                name=data.name,
                cpf=CryptoService.encrypt(data.cpf),
                cpf_hash=cpf_hash,
                cpf_token=cpf_token,
                cpf_last4=cpf_last4,
                email=data.email,
                hashed_password=hashed_pwd,
                mfa_secret=secret,
                mfa_enabled=False,
            )
            db.add(db_user)
            await db.flush()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=400, detail="CPF ou email ja cadastrado.")

        acc_num = None
        for _ in range(10):
            candidate = f"{random.randint(1000, 9999)}-{random.randint(1, 9)}"
            exists = await db.execute(
                select(models.Account.id).where(models.Account.account_number == candidate)
            )
            if not exists.scalar_one_or_none():
                acc_num = candidate
                break
        if not acc_num:
            raise HTTPException(status_code=500, detail="Falha ao gerar numero de conta.")
        account = models.Account(
            account_number=acc_num,
            balance=to_decimal("0.00"),
            blocked_balance=to_decimal("0.00"),
            overdraft_limit=to_decimal("0.00"),
            account_type=data.account_type,
            user_id=db_user.id,
            owner=db_user,
        )
        db.add(account)
        try:
            from src.domain.regulatory import models as regulatory_models  # local import to avoid cycles
            db.add(regulatory_models.KycProfile(user_id=db_user.id, status="PENDING", risk_level="MEDIUM"))
        except Exception:
            pass

        await db.commit()

        stmt = select(models.Account).options(
            selectinload(models.Account.owner),
            selectinload(models.Account.pix_keys),
        ).where(models.Account.id == account.id)

        result = await db.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def authenticate_account(db: AsyncSession, login_identifier: str, password: str):
        user = None

        if login_identifier.isdigit() and len(login_identifier) == 11:
            cpf_hash = hashlib.sha256(login_identifier.encode()).hexdigest()
            stmt = select(models.User).where(models.User.cpf_hash == cpf_hash)
            res = await db.execute(stmt)
            user = res.scalar_one_or_none()

        if not user and login_identifier.isdigit():
            stmt = select(models.Account).options(selectinload(models.Account.owner)).where(
                models.Account.id == int(login_identifier)
            )
            res = await db.execute(stmt)
            account = res.scalar_one_or_none()
            if account:
                user = account.owner

        if not user:
            stmt = select(models.User).where(models.User.email == login_identifier)
            res = await db.execute(stmt)
            user = res.scalar_one_or_none()

        if not user or not security.verify_password(password, user.hashed_password):
            return False

        stmt_acc = select(models.Account).options(
            selectinload(models.Account.owner),
            selectinload(models.Account.pix_keys),
        ).where(models.Account.user_id == user.id)

        result_acc = await db.execute(stmt_acc)
        account = result_acc.scalars().first()
        if account and account.status != "ACTIVE":
            return False
        return account

    @staticmethod
    async def get_account_by_id(db: AsyncSession, account_id: int):
        stmt = select(models.Account).options(selectinload(models.Account.owner)).where(models.Account.id == account_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_transaction_by_id(db: AsyncSession, transaction_id: int):
        stmt = select(models.Transaction).where(models.Transaction.id == transaction_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_accounts(db: AsyncSession, user_id: int):
        stmt = select(models.Account).options(
            selectinload(models.Account.owner),
            selectinload(models.Account.pix_keys),
        ).where(models.Account.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalars().all()

    # --- SEGURANCA & MFA ---
    @staticmethod
    async def enable_mfa(db: AsyncSession, account_id: int, code: str):
        account = await LedgerService.get_account_by_id(db, account_id)
        if not account or not account.owner:
            raise HTTPException(status_code=404, detail="Conta nao encontrada")

        totp = pyotp.TOTP(account.owner.mfa_secret)
        if not totp.verify(code):
            raise HTTPException(status_code=400, detail="Codigo MFA invalido")

        account.owner.mfa_enabled = True

        plain_codes = []
        for _ in range(5):
            raw_code = secrets.token_hex(3).upper()
            plain_codes.append(raw_code)
            code_hash = security.get_password_hash(raw_code)
            db_code = models.BackupCode(user_id=account.owner.id, code_hash=code_hash)
            db.add(db_code)

        await db.commit()
        return plain_codes

    @staticmethod
    async def validate_second_factor(db: AsyncSession, user_id: int, code: str) -> bool:
        stmt = select(models.User).where(models.User.id == user_id)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user or not user.mfa_enabled:
            return True

        totp = pyotp.TOTP(user.mfa_secret)
        if totp.verify(code):
            return True

        stmt_bkp = select(models.BackupCode).where(
            models.BackupCode.user_id == user_id,
            models.BackupCode.used == False,  # noqa: E712
        )
        res_bkp = await db.execute(stmt_bkp)
        for bkp in res_bkp.scalars().all():
            if security.verify_password(code, bkp.code_hash):
                bkp.used = True
                await db.commit()
                return True

        return False

    @staticmethod
    def get_mfa_uri(account_name: str, secret: str) -> str:
        return pyotp.totp.TOTP(secret).provisioning_uri(name=account_name, issuer_name="LuisBank Secure")

    @staticmethod
    async def validate_step_up_auth(db: AsyncSession, account_id: int, amount_units: float, otp_code: str = None):
        if amount_units < MFA_THRESHOLD_UNITS:
            return

        account = await LedgerService.get_account_by_id(db, account_id)
        if account and account.owner:
            if not account.owner.mfa_enabled:
                raise HTTPException(status_code=403, detail="MFA_SETUP_REQUIRED")
            if not otp_code:
                raise HTTPException(status_code=401, detail="MFA_REQUIRED")
            is_valid = await LedgerService.validate_second_factor(db, account.owner.id, otp_code)
            if not is_valid:
                raise HTTPException(status_code=401, detail="Codigo MFA invalido")

    @staticmethod
    async def check_idempotency(namespace: str, key: str):
        cache_key = f"idem:{namespace}:{key}"
        if await cache.get_value(cache_key):
            return True
        await cache.set_value(cache_key, "processed", expire_in_seconds=86400)
        return False

    @staticmethod
    async def _find_transaction_by_idempotency(
        db: AsyncSession, account_id: int, idempotency_key: str
    ) -> models.Transaction | None:
        stmt = select(models.Transaction).where(
            models.Transaction.account_id == account_id,
            models.Transaction.idempotency_key == idempotency_key,
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    # --- CORE BANKING & LEDGER ---
    @staticmethod
    async def get_balance(db: AsyncSession, account_id: int, use_cache: bool = True) -> float:
        cache_key = f"balance:{account_id}"
        if use_cache:
            cached = await cache.get_value(cache_key)
            if cached is not None:
                return to_decimal(cached)

        stmt = select(func.coalesce(func.sum(models.Posting.amount), 0.0)).where(
            models.Posting.account_id == account_id
        )
        res = await db.execute(stmt)
        bal = to_decimal(res.scalar() or 0)

        if bal == 0:
            stmt_acc = select(models.Account).where(models.Account.id == account_id)
            res_acc = await db.execute(stmt_acc)
            acc = res_acc.scalar_one_or_none()
            if acc and acc.balance > 0:
                bal = to_decimal(acc.balance)

        if use_cache:
            await cache.set_value(cache_key, str(bal), expire_in_seconds=60)
        return bal

    @staticmethod
    async def create_transaction(
        db: AsyncSession,
        data: schemas.TransactionCreate,
        otp: str = None,
        fraud_context: dict | None = None,
    ):
        existing = await LedgerService._find_transaction_by_idempotency(
            db, data.account_id, data.idempotency_key
        )
        if existing:
            existing.idempotency_hit = True
            return existing

        try:
            idem_hit = await LedgerService.check_idempotency(str(data.account_id), data.idempotency_key)
        except Exception:
            idem_hit = False
        if idem_hit:
            existing = await LedgerService._find_transaction_by_idempotency(
                db, data.account_id, data.idempotency_key
            )
            if existing:
                existing.idempotency_hit = True
                return existing
            raise HTTPException(status_code=409, detail="Transacao em processamento")

        amount_units = to_decimal(data.amount)

        if fraud_context:
            from src.domain.fraud.engine import FraudEngine
            result = await FraudEngine.evaluate(
                db,
                account_id=data.account_id,
                amount_units=amount_units,
                ip=fraud_context.get("ip", ""),
                user_agent=fraud_context.get("user_agent", ""),
                device_fingerprint=fraud_context.get("device_fingerprint"),
                transaction_id=None,
            )
            if result["action"] == "VERIFY" and not otp:
                raise HTTPException(status_code=401, detail="FRAUD_VERIFICATION_REQUIRED")

        account = await LedgerService._get_account_for_update(db, data.account_id)
        LedgerService._ensure_account_active(account)
        if data.type == "WITHDRAW":
            await LedgerService._ensure_kyc_for_outbound(db, account.user_id, amount_units)
            limits = await LedgerService._get_user_limits(db, account.user_id)
            if amount_units > to_decimal(limits.withdrawal_limit or 0):
                raise HTTPException(status_code=422, detail="Limite de saque excedido")
        await LedgerService.validate_step_up_auth(db, data.account_id, amount_units, otp)

        available = (
            await LedgerService.get_balance(db, data.account_id, use_cache=False)
        ) - to_decimal(account.blocked_balance or 0) + to_decimal(account.overdraft_limit or 0)
        if data.type == "WITHDRAW":
            if available < amount_units:
                raise HTTPException(status_code=422, detail="Saldo insuficiente")

        tx = models.Transaction(
            idempotency_key=data.idempotency_key,
            amount=amount_units,
            description="Transacao",
            operation_type=data.type,
            account_id=data.account_id,
            timestamp=datetime.utcnow(),
        )
        seq, prev_hash, record_hash = await LedgerService._compute_tx_hash(db, tx)
        tx.sequence = seq
        tx.prev_hash = prev_hash
        tx.record_hash = record_hash
        db.add(tx)
        await db.flush()

        sys_acc = await LedgerService._get_system_account(db, for_update=True)
        if data.type == "DEPOSIT":
            postings = [
                models.Posting(transaction_id=tx.id, account_id=data.account_id, amount=amount_units),
                models.Posting(transaction_id=tx.id, account_id=sys_acc.id, amount=-amount_units),
            ]
        else:
            postings = [
                models.Posting(transaction_id=tx.id, account_id=data.account_id, amount=-amount_units),
                models.Posting(transaction_id=tx.id, account_id=sys_acc.id, amount=amount_units),
            ]
        LedgerService._ensure_double_entry(postings)
        db.add_all(postings)

        stmt_acc = select(models.Account).where(models.Account.id == data.account_id)
        res_acc = await db.execute(stmt_acc)
        acc = res_acc.scalar_one_or_none()
        if acc:
            acc.balance = to_decimal(acc.balance or 0) + (amount_units if data.type == "DEPOSIT" else -amount_units)
        sys_acc.balance = to_decimal(sys_acc.balance or 0) + (-amount_units if data.type == "DEPOSIT" else amount_units)

        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            existing = await LedgerService._find_transaction_by_idempotency(
                db, data.account_id, data.idempotency_key
            )
            if existing:
                existing.idempotency_hit = True
                return existing
            raise
        except Exception:
            await db.rollback()
            raise
        await cache.delete_key(f"balance:{data.account_id}")
        if amount_units >= to_decimal(settings.AML_LARGE_TX_THRESHOLD):
            from src.domain.regulatory.services import RegulatoryService
            await RegulatoryService.create_aml_alert(
                db, account.user_id, rule="LARGE_TX", details=f"amount={amount_units}"
            )
        TRANSACTION_COUNT.labels(operation_type=data.type).inc()
        return tx

    @staticmethod
    async def process_transfer(
        db: AsyncSession,
        data: schemas.TransferCreate,
        otp: str = None,
        fraud_context: dict | None = None,
    ):
        if data.from_account_id == data.to_account_id:
            raise HTTPException(status_code=400, detail="Conta de origem e destino iguais")

        existing = await LedgerService._find_transaction_by_idempotency(
            db, data.from_account_id, data.idempotency_key
        )
        if existing:
            existing.idempotency_hit = True
            return existing

        try:
            idem_hit = await LedgerService.check_idempotency(str(data.from_account_id), data.idempotency_key)
        except Exception:
            idem_hit = False
        if idem_hit:
            existing = await LedgerService._find_transaction_by_idempotency(
                db, data.from_account_id, data.idempotency_key
            )
            if existing:
                existing.idempotency_hit = True
                return existing
            raise HTTPException(status_code=409, detail="Transacao em processamento")

        amount_units = to_decimal(data.amount)

        if fraud_context:
            from src.domain.fraud.engine import FraudEngine
            result = await FraudEngine.evaluate(
                db,
                account_id=data.from_account_id,
                amount_units=amount_units,
                ip=fraud_context.get("ip", ""),
                user_agent=fraud_context.get("user_agent", ""),
                device_fingerprint=fraud_context.get("device_fingerprint"),
                transaction_id=None,
            )
            if result["action"] == "VERIFY" and not otp:
                raise HTTPException(status_code=401, detail="FRAUD_VERIFICATION_REQUIRED")

        accounts = await LedgerService._get_accounts_for_update(
            db, [data.from_account_id, data.to_account_id]
        )
        acc_from = accounts.get(data.from_account_id)
        acc_to = accounts.get(data.to_account_id)
        LedgerService._ensure_account_active(acc_from)
        LedgerService._ensure_account_active(acc_to)
        await LedgerService._ensure_kyc_for_outbound(db, acc_from.user_id, amount_units)
        limits = await LedgerService._get_user_limits(db, acc_from.user_id)
        if amount_units > to_decimal(limits.ted_limit or 0):
            raise HTTPException(status_code=422, detail="Limite de transferencia excedido")
        await LedgerService.validate_step_up_auth(db, data.from_account_id, amount_units, otp)

        available = (
            await LedgerService.get_balance(db, data.from_account_id, use_cache=False)
        ) - to_decimal(acc_from.blocked_balance or 0) + to_decimal(acc_from.overdraft_limit or 0)
        if available < amount_units:
            raise HTTPException(status_code=422, detail="Saldo insuficiente")

        tx = models.Transaction(
            idempotency_key=data.idempotency_key,
            amount=amount_units,
            operation_type="TRANSFER",
            description=data.description,
            account_id=data.from_account_id,
            timestamp=datetime.utcnow(),
        )
        seq, prev_hash, record_hash = await LedgerService._compute_tx_hash(db, tx)
        tx.sequence = seq
        tx.prev_hash = prev_hash
        tx.record_hash = record_hash
        db.add(tx)
        await db.flush()

        postings = [
            models.Posting(transaction_id=tx.id, account_id=data.from_account_id, amount=-amount_units),
            models.Posting(transaction_id=tx.id, account_id=data.to_account_id, amount=amount_units),
        ]
        LedgerService._ensure_double_entry(postings)
        db.add_all(postings)

        if acc_from:
            acc_from.balance = to_decimal(acc_from.balance or 0) - amount_units

        if acc_to:
            acc_to.balance = to_decimal(acc_to.balance or 0) + amount_units

        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            existing = await LedgerService._find_transaction_by_idempotency(
                db, data.from_account_id, data.idempotency_key
            )
            if existing:
                existing.idempotency_hit = True
                return existing
            raise
        except Exception:
            await db.rollback()
            raise
        await cache.delete_key(f"balance:{data.from_account_id}")
        await cache.delete_key(f"balance:{data.to_account_id}")
        if amount_units >= to_decimal(settings.AML_LARGE_TX_THRESHOLD):
            from src.domain.regulatory.services import RegulatoryService
            await RegulatoryService.create_aml_alert(
                db, acc_from.user_id, rule="LARGE_TX", details=f"amount={amount_units}"
            )
        TRANSACTION_COUNT.labels(operation_type="TRANSFER").inc()
        return tx

    @staticmethod
    async def verify_integrity(db: AsyncSession) -> dict:
        stmt_sum = select(
            models.Posting.transaction_id,
            func.coalesce(func.sum(models.Posting.amount), 0.0),
        ).group_by(models.Posting.transaction_id)
        res_sum = await db.execute(stmt_sum)
        posting_sums = {tx_id: to_decimal(total) for tx_id, total in res_sum.all()}
        stmt = select(models.Transaction).order_by(models.Transaction.sequence.asc())
        res = await db.execute(stmt)
        txs = res.scalars().all()
        prev_hash = ""
        for tx in txs:
            if posting_sums.get(tx.id, to_decimal("0.00")) != to_decimal("0.00"):
                return {"ok": False, "tx_id": tx.id, "reason": "POSTINGS_IMBALANCE"}
            raw = "|".join([
                str(tx.sequence),
                str(tx.account_id),
                str(tx.amount),
                tx.operation_type,
                tx.description or "",
                tx.timestamp.isoformat(),
                prev_hash or "",
            ])
            expected = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            if tx.record_hash != expected or tx.prev_hash != prev_hash:
                return {"ok": False, "tx_id": tx.id, "reason": "HASH_MISMATCH"}
            prev_hash = tx.record_hash
        return {"ok": True, "count": len(txs)}

    @staticmethod
    async def get_statement(
        db: AsyncSession,
        account_id: int,
        start_date: str | None = None,
        end_date: str | None = None,
        tx_type: str | None = None,
        min_amount: float | None = None,
        max_amount: float | None = None,
        search: str | None = None,
    ) -> dict:
        balance = await LedgerService.get_balance(db, account_id)
        stmt = select(models.Transaction).where(models.Transaction.account_id == account_id)
        if start_date:
            stmt = stmt.where(models.Transaction.timestamp >= datetime.fromisoformat(start_date))
        if end_date:
            stmt = stmt.where(models.Transaction.timestamp <= datetime.fromisoformat(end_date))
        if tx_type:
            stmt = stmt.where(models.Transaction.operation_type == tx_type)
        if min_amount is not None:
            stmt = stmt.where(models.Transaction.amount >= to_decimal(min_amount))
        if max_amount is not None:
            stmt = stmt.where(models.Transaction.amount <= to_decimal(max_amount))
        if search:
            stmt = stmt.where(models.Transaction.description.ilike(f"%{search}%"))

        stmt = stmt.order_by(models.Transaction.timestamp.desc()).limit(50)
        result = await db.execute(stmt)

        history = []
        for tx in result.scalars().all():
            history.append({
                "date": str(tx.timestamp),
                "amount": tx.amount,
                "type": tx.operation_type,
                "description": tx.description,
            })

        return {"account_id": account_id, "balance_current": balance, "transactions": history}

    # --- PIX ---
    @staticmethod
    async def create_pix_key(db: AsyncSession, account_id: int, data: schemas.PixKeyCreate):
        account = await LedgerService.get_account_by_id(db, account_id)
        LedgerService._ensure_account_active(account)
        valid_types = {"CPF", "EMAIL", "PHONE", "EVP"}
        if data.key_type.upper() not in valid_types:
            raise HTTPException(status_code=400, detail="Tipo de chave Pix invalido.")
        stmt = select(models.PixKey).where(models.PixKey.key == data.key)
        existing = await db.execute(stmt)
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Chave Pix ja cadastrada.")

        new_key = models.PixKey(key=data.key, key_type=data.key_type.upper(), account_id=account_id)
        db.add(new_key)
        await db.commit()
        return new_key

    @staticmethod
    async def process_pix_transfer(
        db: AsyncSession,
        data: schemas.PixTransferCreate,
        from_account_id: int,
        otp: str = None,
        fraud_context: dict | None = None,
    ):
        from src.domain.pix.services import PixService
        amount_units = to_decimal(data.amount)
        if fraud_context:
            from src.domain.fraud.engine import FraudEngine
            result = await FraudEngine.evaluate(
                db,
                account_id=from_account_id,
                amount_units=amount_units,
                ip=fraud_context.get("ip", ""),
                user_agent=fraud_context.get("user_agent", ""),
                device_fingerprint=fraud_context.get("device_fingerprint"),
                transaction_id=None,
            )
            if result["action"] == "VERIFY" and not otp:
                raise HTTPException(status_code=401, detail="FRAUD_VERIFICATION_REQUIRED")
        await PixService._enforce_limits(db, from_account_id, amount_units)
        stmt = select(models.PixKey).where(models.PixKey.key == data.pix_key)
        result = await db.execute(stmt)
        pix_entry = result.scalar_one_or_none()

        if not pix_entry:
            raise HTTPException(status_code=404, detail="Chave Pix nao encontrada.")

        internal_transfer_data = schemas.TransferCreate(
            from_account_id=from_account_id,
            to_account_id=pix_entry.account_id,
            amount=data.amount,
            idempotency_key=data.idempotency_key,
        )

        return await LedgerService.process_transfer(db, internal_transfer_data, otp)
