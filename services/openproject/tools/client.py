import os
import base64
import requests
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from dotenv import load_dotenv
    env_path = Path("/mnt/expansion/desplegados/sos-mcp-services/.env")
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

class OpenProjectClient:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = (base_url or os.getenv("OPENPROJECT_URL", "http://127.0.0.1:8085/openproject")).rstrip("/")
        self.api_key = api_key or os.getenv("OPENPROJECT_API_KEY", "")
        self.host_header = os.getenv("OPENPROJECT_HOST_HEADER", "dinamica1.fciencias.unam.mx")

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Host": self.host_header,
            "X-Forwarded-Proto": "https"
        }
        if self.api_key:
            auth_str = f"apikey:{self.api_key}"
            encoded = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
            headers["Authorization"] = f"Basic {encoded}"
        return headers

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        resp = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        resp = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def patch(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        resp = requests.patch(url, headers=self._get_headers(), json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def delete(self, endpoint: str) -> bool:
        url = f"{self.base_url}{endpoint}"
        resp = requests.delete(url, headers=self._get_headers(), timeout=30)
        resp.raise_for_status()
        return True
