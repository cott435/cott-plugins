"""The end-to-end path of data/ingest: fetch_bars over a fake client."""

import logging
from datetime import date


def test_fetch_bars_end_to_end(make_client, sample_payload, caplog):
    """Design §4 workflow: path, params, three bars and one INFO record event=data.ingest.fetch."""
    from data.ingest.fetch import fetch_bars

    client = make_client([sample_payload])
    with caplog.at_level(logging.INFO, logger="data.ingest"):
        bars = fetch_bars("AAPL", date(2024, 3, 4), date(2024, 3, 6), client=client)
    assert len(bars) == 3
    path, params = client.calls[0]
    assert path == "/v2/aggs/ticker/AAPL/range/1/day/2024-03-04/2024-03-06"
    assert params == {"adjusted": "true", "sort": "asc"}
    infos = [
        r
        for r in caplog.records
        if r.levelno >= logging.INFO and r.name == "data.ingest"
    ]
    assert len(infos) == 1
    assert infos[0].getMessage() == "event=data.ingest.fetch symbol=AAPL bars=3"
