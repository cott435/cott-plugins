"""The package's base exception and the rejection `ingest` raises."""


class DataError(Exception):
    """Base exception of the `data` package."""


class IngestError(DataError):
    """A data row of the CSV export that could not be read as a trade.

    Attributes:
        row: The 1-based data row number; the header line is not counted.
        field: The column whose value was rejected.
        reason: Why the value was rejected.
    """

    def __init__(self, row: int, field: str, reason: str) -> None:
        """Build the error; its message names the row, the field and the reason.

        Args:
            row: The 1-based data row number.
            field: The column whose value was rejected.
            reason: Why the value was rejected.
        """
        super().__init__(f"row {row}: field {field!r}: {reason}")
        self.row = row
        self.field = field
        self.reason = reason
