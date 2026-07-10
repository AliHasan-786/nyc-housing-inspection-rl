"""Small, injectable Socrata client with pagination and bounded retries."""

from __future__ import annotations

import time
from collections.abc import Iterator, Mapping
from typing import Any

import httpx

JsonRow = dict[str, Any]


class SocrataError(RuntimeError):
    """Raised when a source request cannot be completed safely."""


class SocrataClient:
    def __init__(
        self,
        *,
        domain: str = "data.cityofnewyork.us",
        app_token: str | None = None,
        page_size: int = 50_000,
        max_retries: int = 3,
        timeout_seconds: float = 60.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if page_size <= 0:
            raise ValueError("page_size must be positive")
        self.domain = domain
        self.page_size = page_size
        self.max_retries = max_retries
        headers = {"User-Agent": "civic-inspection-lab/0.1"}
        if app_token:
            headers["X-App-Token"] = app_token
        self._client = httpx.Client(
            headers=headers,
            timeout=timeout_seconds,
            transport=transport,
            follow_redirects=True,
        )

    def __enter__(self) -> SocrataClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def iter_pages(
        self, dataset_id: str, params: Mapping[str, str] | None = None
    ) -> Iterator[list[JsonRow]]:
        """Yield pages until Socrata returns fewer rows than the requested limit."""

        base_params = dict(params or {})
        offset = 0
        while True:
            request_params = {
                **base_params,
                "$limit": str(self.page_size),
                "$offset": str(offset),
            }
            rows = self._get(dataset_id, request_params)
            if rows:
                yield rows
            if len(rows) < self.page_size:
                return
            offset += len(rows)

    def _get(self, dataset_id: str, params: Mapping[str, str]) -> list[JsonRow]:
        url = f"https://{self.domain}/resource/{dataset_id}.json"
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, list) or not all(
                    isinstance(item, dict) for item in payload
                ):
                    raise SocrataError(f"Unexpected payload for dataset {dataset_id}")
                return payload
            except (httpx.HTTPError, ValueError, SocrataError) as error:
                last_error = error
                retryable = not isinstance(error, httpx.HTTPStatusError) or (
                    error.response.status_code == 429 or error.response.status_code >= 500
                )
                if attempt >= self.max_retries or not retryable:
                    break
                time.sleep(min(2**attempt, 8))
        raise SocrataError(f"Failed to fetch dataset {dataset_id}") from last_error
