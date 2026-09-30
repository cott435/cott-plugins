"""ingest — read the CSV export into Trade records."""

from data.ingest.model import Trade
from data.ingest.reader import read_export

__all__ = ["Trade", "read_export"]
