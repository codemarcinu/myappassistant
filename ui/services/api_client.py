from typing import Any, Dict, Optional

import requests  # type: ignore
from requests.adapters import HTTPAdapter, Retry  # type: ignore

from ui.config import Config


class ApiClient:
    """Klient API z obsługą retry logic i błędów."""

    def __init__(
        self, base_url: str = Config.BACKEND_URL, retries: int = 3, backoff: float = 0.5
    ) -> None:
        self.base_url = base_url
        self.session = requests.Session()
        retry_strategy = Retry(
            total=retries,
            backoff_factor=backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=[
                "HEAD",
                "GET",
                "OPTIONS",
                "POST",
            ],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def post(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> Any:
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.post(
                url,
                json=json,
                files=files,
                data=data,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: int = 30
    ) -> Any:
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
