"""Read trades from CSV into `Trade` rows."""

from data.ingest.loader import IngestError, Trade, load_trades

__all__ = ["IngestError", "Trade", "load_trades"]
