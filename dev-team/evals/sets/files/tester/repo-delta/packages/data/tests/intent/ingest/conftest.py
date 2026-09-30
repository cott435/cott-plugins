"""Fixtures for the data/ingest intent tests: the probe sample and a fake vendor client."""

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


class FakeClient:
    """A VendorClient built to design §5: a queue of payloads or exceptions to raise."""

    def __init__(self, responses: list[Any]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, dict[str, str]]] = []

    def get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        self.calls.append((path, dict(params)))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


@pytest.fixture
def sample_payload() -> dict[str, Any]:
    """The three AAPL sessions recorded by docs/sources/polygon.md."""
    return json.loads((FIXTURES / "polygon.sample.json").read_text())


@pytest.fixture
def make_client():
    """Build a FakeClient from a list of responses."""

    def _make(responses: list[Any]) -> FakeClient:
        return FakeClient(responses)

    return _make
