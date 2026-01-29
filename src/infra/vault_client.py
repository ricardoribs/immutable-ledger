import os
from typing import Optional

try:
    import hvac
except Exception:  # pragma: no cover - optional dependency
    hvac = None


class VaultClient:
    def __init__(self, addr: str, token: str, timeout: int = 2):
        if not hvac:
            raise RuntimeError("hvac not installed")
        self._client = hvac.Client(url=addr, token=token, timeout=timeout)

    def read_kv2(self, mount: str, path: str) -> Optional[dict]:
        try:
            resp = self._client.secrets.kv.v2.read_secret_version(mount_point=mount, path=path)
        except Exception:
            return None
        data = resp.get("data", {}).get("data", {})
        return data or None


def get_vault_client() -> Optional[VaultClient]:
    addr = os.getenv("VAULT_ADDR")
    token = os.getenv("VAULT_TOKEN")
    timeout = int(os.getenv("VAULT_TIMEOUT_SECONDS", "2"))
    if not addr or not token:
        return None
    try:
        return VaultClient(addr, token, timeout=timeout)
    except Exception:
        return None
