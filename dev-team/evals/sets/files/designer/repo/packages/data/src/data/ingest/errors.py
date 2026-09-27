class DataError(Exception):
    def __init__(self, code: str, message: str, context: dict[str, object] | None = None):
        super().__init__(message)
        self.code, self.message, self.context = code, message, context or {}


class IngestError(DataError):
    pass
