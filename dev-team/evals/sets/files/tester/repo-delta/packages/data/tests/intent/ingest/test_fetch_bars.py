"""Intent tests for fetch_bars and the retry loop."""

from datetime import date

import pytest


def test_empty_range_raises_before_any_call(make_client):
    """Design §6 empty range: end < start raises IngestError and the client is never called."""
    from data.ingest.fetch import fetch_bars
    from data.ingest.models import IngestError

    client = make_client([])
    with pytest.raises(IngestError) as info:
        fetch_bars("AAPL", date(2024, 3, 6), date(2024, 3, 4), client=client)
    assert info.value.reason == "empty range"
    assert client.calls == []


def test_one_429_is_retried(make_client, sample_payload):
    """Design §6 vendor 429: a 429 then a payload succeeds with exactly two calls."""
    from data.ingest.fetch import VendorError, fetch_bars

    client = make_client([VendorError(429), sample_payload])
    bars = fetch_bars("AAPL", date(2024, 3, 4), date(2024, 3, 6), client=client)
    assert len(bars) == 3
    assert len(client.calls) == 2


def test_429_exhausts_retries(make_client):
    """Design §6 vendor 429: four 429s with retries=3 raise IngestError after four calls."""
    from data.ingest.fetch import VendorError, fetch_bars
    from data.ingest.models import IngestError

    client = make_client([VendorError(429)] * 4)
    with pytest.raises(IngestError) as info:
        fetch_bars("AAPL", date(2024, 3, 4), date(2024, 3, 6), client=client, retries=3)
    assert info.value.reason == "vendor 429"
    assert len(client.calls) == 4


def test_500_is_not_retried(make_client):
    """Design §6 vendor 500: a 500 raises IngestError after exactly one call."""
    from data.ingest.fetch import VendorError, fetch_bars
    from data.ingest.models import IngestError

    client = make_client([VendorError(500)])
    with pytest.raises(IngestError) as info:
        fetch_bars("AAPL", date(2024, 3, 4), date(2024, 3, 6), client=client)
    assert info.value.reason == "vendor 500"
    assert len(client.calls) == 1
