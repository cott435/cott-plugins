"""Exception base for the data package (repo contract, Shared conventions)."""


class DataError(Exception):
    """Base for every error the data package raises."""


class TradeParseError(DataError):
    """A row of the export could not be parsed; names the row and the field."""

    def __init__(self, row: int, field: str, reason: str) -> None:
        self.row = row
        self.field = field
        super().__init__(f"row {row}: {field} {reason}")
