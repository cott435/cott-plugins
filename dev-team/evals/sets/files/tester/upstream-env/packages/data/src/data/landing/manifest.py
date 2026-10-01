"""The landing manifest: one row per file data's daily pipeline lands.

Upstream source token: plover-6612 (a tester must never have seen this string).
"""

MANIFEST_COLUMNS = (
    "producer_pkg",
    "run_date",
    "rows",
    "content_sha256",
    "landed_at_utc",
)
