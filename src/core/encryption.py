from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.fernet import Fernet
from src.core.config import settings
from src.infra.vault_client import get_vault_client

import base64
import hashlib
import os


_cached_key: bytes | None = None


def _normalize_key(raw: bytes) -> bytes:
    if len(raw) == 32:
        return raw
    return hashlib.sha256(raw).digest()


def _load_key_from_vault() -> bytes | None:
    client = get_vault_client()
    if not client:
        return None
    data = client.read_kv2(settings.VAULT_KV_MOUNT, settings.VAULT_ENCRYPTION_KEY_PATH)
    if not data:
        return None
    value = data.get(settings.VAULT_ENCRYPTION_KEY_FIELD)
    if not value:
        return None
    try:
        return base64.urlsafe_b64decode(value.encode())
    except Exception:
        return value.encode()


def _get_key() -> bytes:
    global _cached_key
    if _cached_key:
        return _cached_key

    vault_key = _load_key_from_vault()
    if vault_key:
        _cached_key = _normalize_key(vault_key)
        return _cached_key

    try:
        raw = base64.urlsafe_b64decode(settings.ENCRYPTION_KEY.encode())
    except Exception:
        raw = settings.ENCRYPTION_KEY.encode()
    _cached_key = _normalize_key(raw)
    return _cached_key


def get_cipher():
    # Legado (Fernet) para compatibilidade com dados antigos
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


class CryptoService:
    @staticmethod
    def encrypt(data: str) -> str:
        if not data:
            return ""
        key = _get_key()
        nonce = os.urandom(12)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, data.encode(), None)
        token = base64.b64encode(nonce + ciphertext).decode("ascii")
        return f"v1:{token}"

    @staticmethod
    def decrypt(token: str) -> str:
        if not token:
            return ""
        try:
            if token.startswith("v1:"):
                raw = base64.b64decode(token.split("v1:", 1)[1])
                nonce = raw[:12]
                ciphertext = raw[12:]
                aesgcm = AESGCM(_get_key())
                return aesgcm.decrypt(nonce, ciphertext, None).decode()
            return get_cipher().decrypt(token.encode()).decode()
        except Exception:
            return "ERROR_DECRYPT"
