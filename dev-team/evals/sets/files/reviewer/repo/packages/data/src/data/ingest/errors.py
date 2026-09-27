"""Errors raised by the ingest section."""


class VendorUnavailable(RuntimeError):
    """The vendor kept answering 429 after every retry."""

    def __init__(self, symbol: str) -> None:
        super().__init__(f"vendor unavailable for {symbol}")
        self.symbol = symbol
