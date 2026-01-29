from src.domain.security.services import SecurityService
from src.core.security import get_password_hash, verify_password


def test_device_fingerprint_deterministic():
    fp1 = SecurityService.compute_device_fingerprint("ua", "pt-BR", "1.2.3.4")
    fp2 = SecurityService.compute_device_fingerprint("ua", "pt-BR", "1.2.3.4")
    assert fp1 == fp2


def test_password_hash_verify():
    h = get_password_hash("secret")
    assert verify_password("secret", h)
