"""Errors raised by the clean section."""


class MissingColumns(ValueError):
    """A BarFrame column the clean rules need is absent."""

    def __init__(self, missing: list[str]) -> None:
        super().__init__(f"missing columns: {', '.join(missing)}")
        self.missing = missing


class EmptyBars(ValueError):
    """The frame has no rows, so there is nothing to clean."""
