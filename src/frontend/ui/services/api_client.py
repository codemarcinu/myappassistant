from json.decoder import JSONDecodeError
from typing import Any, Dict, Optional

import httpx
import streamlit as st

from ..config import Config


class ApiClient:
    """Client for interacting with the backend API."""

    def __init__(self) -> None:
        """Initialize the API client with the base URL from config."""
        self.base_url = Config.API_BASE_URL
        self.timeout = Config.API_TIMEOUT

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a GET request to the API.

        Args:
            endpoint: API endpoint to call (e.g., "/api/v1/products")
            params: Query parameters to include in the request

        Returns:
            Response data as a dictionary
        """
        try:
            url = f"{self.base_url}{endpoint}"
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            st.error(f"HTTP error: {e}")
            return {"error": str(e)}
        except httpx.RequestError as e:
            st.error(f"Request error: {e}")
            return {"error": f"Nie można połączyć się z API: {str(e)}"}
        except JSONDecodeError:
            st.error("Nieprawidłowa odpowiedź z API")
            return {"error": "Nieprawidłowa odpowiedź z API"}
        except Exception as e:
            st.error(f"Nieznany błąd: {e}")
            return {"error": str(e)}

    def post(
        self, endpoint: str, json: Optional[Dict[str, Any]] = None, data: Any = None
    ) -> Dict[str, Any]:
        """
        Make a POST request to the API.

        Args:
            endpoint: API endpoint to call (e.g., "/api/v1/products")
            json: JSON data to include in the request body
            data: Form data to include in the request

        Returns:
            Response data as a dictionary
        """
        try:
            url = f"{self.base_url}{endpoint}"
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=json, data=data)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            st.error(f"HTTP error: {e}")
            return {"error": str(e)}
        except httpx.RequestError as e:
            st.error(f"Request error: {e}")
            return {"error": f"Nie można połączyć się z API: {str(e)}"}
        except JSONDecodeError:
            st.error("Nieprawidłowa odpowiedź z API")
            return {"error": "Nieprawidłowa odpowiedź z API"}
        except Exception as e:
            st.error(f"Nieznany błąd: {e}")
            return {"error": str(e)}
