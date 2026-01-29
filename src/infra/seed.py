import os
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.ledger import models
from src.core import security
from src.core.encryption import CryptoService
from src.domain.security.tokenization import TokenizationService
from src.domain.investments import models as investment_models
from src.domain.support import models as support_models
from src.core.config import settings
from src.core.money import to_decimal


async def seed_dev(db: AsyncSession) -> None:
    if os.getenv("SEED_DEV", "false").lower() != "true":
        return

    email = os.getenv("SEED_EMAIL", "dev@luisbank.local")
    password = os.getenv("SEED_PASSWORD", "dev123")
    cpf = os.getenv("SEED_CPF", "00000000000")
    name = os.getenv("SEED_NAME", "Dev User")

    stmt = select(models.User).where(models.User.email == email)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        return

    user = models.User(
        name=name,
        cpf=CryptoService.encrypt(cpf),
        cpf_hash=hashlib.sha256(cpf.encode()).hexdigest(),
        cpf_token=await TokenizationService.tokenize(db, cpf, token_type="CPF", user_id=None, last4=cpf[-4:]),
        cpf_last4=cpf[-4:],
        email=email,
        hashed_password=security.get_password_hash(password),
        mfa_secret="",
        mfa_enabled=False,
    )
    db.add(user)
    await db.flush()

    account = models.Account(
        account_number="0001-0",
        balance=to_decimal("1000.00"),
        blocked_balance=to_decimal("0.00"),
        overdraft_limit=to_decimal("0.00"),
        account_type="CHECKING",
        user_id=user.id,
        owner=user,
    )
    db.add(account)
    await db.commit()

    stmt_prod = select(investment_models.InvestmentProduct)
    res_prod = await db.execute(stmt_prod)
    if not res_prod.scalars().first():
        db.add_all([
            investment_models.InvestmentProduct(name="CDB Liquidez", product_type="CDB", rate=0.12, liquidity="D+0"),
            investment_models.InvestmentProduct(name="Tesouro Selic", product_type="TESOURO", rate=0.10, liquidity="D+1"),
            investment_models.InvestmentProduct(name="Fundo Renda Fixa", product_type="FUND", rate=0.09, liquidity="D+3"),
        ])
        await db.commit()

    stmt_faq = select(support_models.Faq)
    res_faq = await db.execute(stmt_faq)
    if not res_faq.scalars().first():
        db.add_all([
            support_models.Faq(question="Como habilitar MFA?", answer="Acesse Seguranca > MFA e siga o QR Code."),
            support_models.Faq(question="Como fazer PIX?", answer="Use a aba PIX para transferencias instantaneas."),
            support_models.Faq(question="Como pagar boleto?", answer="Acesse Pagamentos > Boletos e use o codigo de barras."),
        ])
        await db.commit()

    stmt_sys = select(models.User).where(models.User.email == settings.SYSTEM_USER_EMAIL)
    res_sys = await db.execute(stmt_sys)
    if not res_sys.scalar_one_or_none():
        sys_user = models.User(
            name="System",
            cpf="",
            cpf_hash=f"system_{settings.SYSTEM_USER_EMAIL}",
            cpf_token=None,
            cpf_last4=None,
            email=settings.SYSTEM_USER_EMAIL,
            hashed_password=security.get_password_hash("system"),
            mfa_secret="",
            mfa_enabled=False,
        )
        db.add(sys_user)
        await db.flush()
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
        await db.commit()
