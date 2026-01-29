from src.core.encryption import CryptoService


def test_encrypt_decrypt_roundtrip():
    data = "12345678901"
    enc = CryptoService.encrypt(data)
    dec = CryptoService.decrypt(enc)
    assert dec == data
