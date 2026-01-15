import os
from typing import Any, Dict, List, Optional

import requests


class CocoonClient:
    """Minimal HTTP client for Cocoon OpenAI-compatible endpoints."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 120.0) -> None:
        self.base_url = (base_url or os.getenv("COCOON_CLIENT_URL", "http://localhost:8081")).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def list_models(self) -> Dict[str, Any]:
        return self._request("GET", "/v1/models")

    def chat_completions(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        max_tokens: Optional[int] = None,
        **extra: Any,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"model": model, "messages": messages}
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        payload.update(extra)
        return self._request("POST", "/v1/chat/completions", json=payload)

    def completions(
        self,
        prompt: str,
        model: str,
        max_tokens: Optional[int] = None,
        **extra: Any,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"model": model, "prompt": prompt}
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        payload.update(extra)
        return self._request("POST", "/v1/completions", json=payload)

    def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        response = self.session.request(method, url, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        if not response.content:
            return {}
        return response.json()
