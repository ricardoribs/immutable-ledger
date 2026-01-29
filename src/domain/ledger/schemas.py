from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional, List
from datetime import datetime

# --- AUTH & TOKENS ---
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str


class LoginRequest(BaseModel):
    username: str  # Pode ser ID da conta ou email
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# --- CADASTRO ---
class AccountCreate(BaseModel):
    name: str
    cpf: str
    email: EmailStr
    password: str
    account_type: str = "CHECKING"

    @field_validator("cpf")
    @classmethod
    def normalize_cpf(cls, value: str) -> str:
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) != 11:
            raise ValueError("CPF invalido.")
        return digits

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Senha deve ter ao menos 8 caracteres.")
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Senha excede o limite maximo permitido.")
        return value

    @field_validator("account_type")
    @classmethod
    def validate_account_type(cls, value: str) -> str:
        allowed = {"CHECKING", "SAVINGS", "SALARY", "DIGITAL", "INVESTMENT"}
        normalized = value.strip().upper()
        if normalized not in allowed:
            raise ValueError("Tipo de conta invalido.")
        return normalized


# --- TRANSACAO GERAL ---
class TransactionCreate(BaseModel):
    account_id: int
    amount: float
    type: str  # "DEPOSIT", "WITHDRAW"
    idempotency_key: str

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Valor deve ser positivo.")
        return value

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        allowed = {"DEPOSIT", "WITHDRAW"}
        normalized = value.strip().upper()
        if normalized not in allowed:
            raise ValueError("Tipo de transacao invalido.")
        return normalized

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency_key(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Chave de idempotencia invalida.")
        return value.strip()


# --- TRANSFERENCIA INTERNA (Conta -> Conta) ---
class TransferCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float
    idempotency_key: str
    description: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Valor deve ser positivo.")
        return value

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency_key(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Chave de idempotencia invalida.")
        return value.strip()

    @model_validator(mode="after")
    def validate_accounts(self):
        if self.from_account_id == self.to_account_id:
            raise ValueError("Conta de origem e destino iguais.")
        return self


# --- PIX ---
class PixKeyCreate(BaseModel):
    key: str
    key_type: str  # "EMAIL", "CPF", "PHONE", "EVP"


class PixKeyResponse(BaseModel):
    key: str
    key_type: str
    created_at: datetime
    active: bool

    class Config:
        from_attributes = True


class PixTransferCreate(BaseModel):
    pix_key: str  # A chave de destino
    amount: float  # Valor em reais (ex: 10.00 = R$ 10,00)
    idempotency_key: str

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Valor deve ser positivo.")
        return value

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency_key(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Chave de idempotencia invalida.")
        return value.strip()


# --- LEITURA (Respostas da API) ---
class TransactionResponse(BaseModel):
    id: int
    amount: float
    description: Optional[str] = None  # Aceita nulo
    timestamp: datetime

    class Config:
        from_attributes = True


class AccountResponse(BaseModel):
    id: int
    account_number: str
    balance: float
    name: str
    cpf_masked: Optional[str] = None
    mfa_enabled: bool = False
    pix_keys: List[PixKeyResponse] = []
    account_type: str = "CHECKING"
    blocked_balance: float = 0.0
    overdraft_limit: float = 0.0

    class Config:
        from_attributes = True
