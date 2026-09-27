"""Intent tests for parse_bars."""

from datetime import UTC, datetime

import pytest


def test_parse_sample_ascending_utc(sample_payload):
    """Design §5 parse_bars: the sample parses to three Bar rows ascending, tz-aware UTC (D1)."""
    from data.ingest.parse import parse_bars

    bars = parse_bars(sample_payload, "AAPL")
    assert len(bars) == 3
    assert [b.ts for b in bars] == sorted(b.ts for b in bars)
    assert all(
        b.ts.tzinfo is not None and b.ts.utcoffset().total_seconds() == 0 for b in bars
    )
    assert bars[0].ts == datetime(2024, 3, 4, 5, tzinfo=UTC)
    assert bars[0].open == 176.15
    assert bars[0].volume == 81510101


def test_parse_reversed_results_still_ascending(sample_payload):
    """Design §4 step 3: results given in reverse order still come back ascending by ts."""
    from data.ingest.parse import parse_bars

    sample_payload["results"].reverse()
    bars = parse_bars(sample_payload, "AAPL")
    assert [b.ts for b in bars] == sorted(b.ts for b in bars)


def test_parse_missing_results_raises(sample_payload):
    """Design §6 missing results: a payload with no results key raises IngestError."""
    from data.ingest.models import IngestError
    from data.ingest.parse import parse_bars

    del sample_payload["results"]
    with pytest.raises(IngestError) as info:
        parse_bars(sample_payload, "AAPL")
    assert info.value.reason == "missing results"
    assert info.value.symbol == "AAPL"


def test_parse_negative_volume_raises(sample_payload):
    """Design §6 negative volume: a row with v == -1 raises IngestError, no partial result."""
    from data.ingest.models import IngestError
    from data.ingest.parse import parse_bars

    sample_payload["results"][1]["v"] = -1
    with pytest.raises(IngestError) as info:
        parse_bars(sample_payload, "AAPL")
    assert info.value.reason == "negative volume"


@pytest.mark.xfail(
    strict=False, reason="D2 open — assumption: zero-volume bars are kept"
)
def test_parse_zero_volume_kept(sample_payload):
    """Design §6 zero volume: a row with v == 0 is kept unchanged (D2 assumption)."""
    from data.ingest.parse import parse_bars

    sample_payload["results"][2]["v"] = 0
    bars = parse_bars(sample_payload, "AAPL")
    assert len(bars) == 3
    assert bars[2].volume == 0
