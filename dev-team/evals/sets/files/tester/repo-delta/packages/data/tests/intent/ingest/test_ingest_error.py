"""Intent tests for IngestError."""


def test_ingest_error_carries_reason_and_symbol():
    """Design §5 IngestError: str() is 'reason: symbol' and .reason/.symbol are set."""
    from data.ingest.models import IngestError

    err = IngestError("missing results", "AAPL")
    assert str(err) == "missing results: AAPL"
    assert err.reason == "missing results"
    assert err.symbol == "AAPL"
