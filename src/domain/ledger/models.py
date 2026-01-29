from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, UniqueConstraint, event
from sqlalchemy.orm import relationship
from src.infra.database import Base
from datetime import datetime
from src.domain.common.types import Money

# --- USUARIOS & AUTH ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    cpf = Column(String, unique=True, index=True, nullable=False)  # Criptografado
    cpf_hash = Column(String, unique=True, index=True, nullable=True)
    cpf_token = Column(String, unique=True, index=True, nullable=True)
    cpf_last4 = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_anonymized = Column(Boolean, default=False)
    anonymized_at = Column(DateTime, nullable=True)

    # Seguranca
    mfa_secret = Column(String, nullable=True)
    mfa_enabled = Column(Boolean, default=False)

    # Relacionamentos
    accounts = relationship("Account", back_populates="owner")
    backup_codes = relationship("BackupCode", back_populates="user")


class BackupCode(Base):
    __tablename__ = "backup_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    code_hash = Column(String, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="backup_codes")


# --- CONTAS & LEDGER ---
class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String, unique=True, index=True)
    balance = Column(Money, default=0)  # Cache de leitura
    blocked_balance = Column(Money, default=0)
    overdraft_limit = Column(Money, default=0)
    account_type = Column(String, default="CHECKING")  # CHECKING, SAVINGS, SALARY, DIGITAL, INVESTMENT
    status = Column(String, default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="accounts")

    postings = relationship("Posting", back_populates="account")
    transactions = relationship("Transaction", back_populates="account")

    # Relacionamento com chaves PIX
    pix_keys = relationship("PixKey", back_populates="account")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("account_id", "idempotency_key", name="uq_transactions_account_idempotency_key"),
        UniqueConstraint("sequence", name="uq_transactions_sequence"),
    )

    id = Column(Integer, primary_key=True, index=True)
    idempotency_key = Column(String, index=True)
    amount = Column(Money, nullable=False)
    operation_type = Column(String, nullable=False)  # DEPOSIT, TRANSFER, PIX, WITHDRAW
    description = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sequence = Column(Integer, index=True, nullable=True)
    prev_hash = Column(String, nullable=True)
    record_hash = Column(String, nullable=True, index=True)

    account_id = Column(Integer, ForeignKey("accounts.id"))  # Quem iniciou
    account = relationship("Account", back_populates="transactions")

    postings = relationship("Posting", back_populates="transaction")


class Posting(Base):
    __tablename__ = "postings"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    account_id = Column(Integer, ForeignKey("accounts.id"))
    amount = Column(Money, nullable=False)  # +Credito / -Debito
    timestamp = Column(DateTime, default=datetime.utcnow)

    transaction = relationship("Transaction", back_populates="postings")
    account = relationship("Account", back_populates="postings")


# --- PIX ---
class PixKey(Base):
    __tablename__ = "pix_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    key_type = Column(String, nullable=False)  # "CPF", "EMAIL", "PHONE", "EVP"

    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    account = relationship("Account", back_populates="pix_keys")

    created_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)


# --- AUDITORIA ---
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=True)
    action = Column(String, nullable=False)
    method = Column(String, nullable=True)
    path = Column(String, nullable=True)
    details = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    prev_hash = Column(String, nullable=True)
    record_hash = Column(String, nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class LedgerSequence(Base):
    __tablename__ = "ledger_sequence"

    id = Column(Integer, primary_key=True)
    value = Column(Integer, default=0, nullable=False)


def _prevent_update_delete(mapper, connection, target):
    raise RuntimeError("Ledger is append-only: updates/deletes are not allowed")


event.listen(Transaction, "before_update", _prevent_update_delete)
event.listen(Transaction, "before_delete", _prevent_update_delete)
event.listen(Posting, "before_update", _prevent_update_delete)
event.listen(Posting, "before_delete", _prevent_update_delete)
