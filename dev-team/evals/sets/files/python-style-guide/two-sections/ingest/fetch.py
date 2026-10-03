"""Requests to the vendor for the `ingest` section.

Entry point: `fetch_day`, one request for one account and one trading day.
"""

from __future__ import annotations

from datetime import date

from data.ingest.models import Bar
from data.vendor import VendorClient, VendorTimeout

_MAX_ATTEMPTS = 3


def fetch_day(client: VendorClient, account: str, day: date) -> list[Bar]:
    """Download one account's bars for one trading day from the vendor.

    A request that times out is sent again, up to three times in all.

    Args:
        client: The vendor client the request is sent with.
        account: The vendor's account identifier.
        day: The trading day to download.

    Returns:
        The day's bars in the order the vendor returned them.

    Raises:
        VendorTimeout: Every attempt timed out.
    """
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            page = client.download(account, day)
        except VendorTimeout:
            if attempt == _MAX_ATTEMPTS:
                raise
        else:
            return [Bar.from_vendor(row) for row in page.rows]
    raise AssertionError("unreachable")
