"""Pluggable, OpenAI-shaped embeddings client.

Every supported provider (Jina default, OpenAI, Voyage, Gemini's compat
endpoint) speaks the same ``POST {base}/embeddings`` protocol, so one client
serves all of them — switching is a matter of base URL + model + dim + key.
Jina's optional ``task`` hint (asymmetric query/passage embeddings) is sent
only when configured, so leaving the task settings blank keeps the payload
valid for providers that reject unknown fields.
"""

from __future__ import annotations

import logging

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


class EmbeddingError(RuntimeError):
    """Provider unusable (missing key) or returned an unexpected payload."""


class Embedder:
    def __init__(
        self,
        *,
        api_base: str,
        model: str,
        api_key: str,
        dim: int,
        timeout: float,
        batch_size: int,
        query_task: str = "",
        passage_task: str = "",
    ) -> None:
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.dim = dim
        self.timeout = timeout
        self.batch_size = max(1, batch_size)
        self.query_task = query_task
        self.passage_task = passage_task

    async def _embed_batch(
        self, client: httpx.AsyncClient, inputs: list[str], task: str
    ) -> list[list[float]]:
        payload: dict = {"model": self.model, "input": inputs}
        if task:
            payload["task"] = task
        resp = await client.post(
            f"{self.api_base}/embeddings",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        if resp.status_code != 200:
            raise EmbeddingError(
                f"{self.model} embeddings HTTP {resp.status_code}: "
                f"{resp.text[:200]}"
            )
        data = resp.json().get("data")
        if not isinstance(data, list) or len(data) != len(inputs):
            raise EmbeddingError("Malformed embeddings response (data mismatch)")
        # Providers may return out of order; the "index" field is authoritative.
        ordered = sorted(data, key=lambda d: d.get("index", 0))
        vectors = [d["embedding"] for d in ordered]
        for v in vectors:
            if len(v) != self.dim:
                raise EmbeddingError(
                    f"Embedding dim {len(v)} != configured {self.dim}; "
                    "set EMBEDDING_DIM to match the model."
                )
        return vectors

    async def _embed(self, texts: list[str], task: str) -> list[list[float]]:
        if not texts:
            return []
        out: list[list[float]] = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for i in range(0, len(texts), self.batch_size):
                out.extend(
                    await self._embed_batch(client, texts[i : i + self.batch_size], task)
                )
        return out

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._embed(texts, self.passage_task)

    async def embed_query(self, text: str) -> list[float]:
        return (await self._embed([text], self.query_task))[0]


def get_embedder() -> Embedder:
    if not settings.embedding_api_key:
        raise EmbeddingError(
            "EMBEDDING_API_KEY is not set. Add your embedding provider key to "
            ".env before running ingestion or retrieval."
        )
    return Embedder(
        api_base=settings.embedding_api_base,
        model=settings.embedding_model,
        api_key=settings.embedding_api_key,
        dim=settings.embedding_dim,
        timeout=settings.embedding_timeout,
        batch_size=settings.embedding_batch_size,
        query_task=settings.embedding_query_task,
        passage_task=settings.embedding_passage_task,
    )
