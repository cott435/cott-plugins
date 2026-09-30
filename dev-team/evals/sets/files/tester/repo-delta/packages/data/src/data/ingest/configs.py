"""Settings for data.ingest."""

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class IngestSettings:
    """Read once from the environment by the surface section's client."""

    vendor_key: str = field(default_factory=lambda: os.environ.get("DATA_VENDOR_KEY", ""))
    retries: int = 3
    base_url: str = "https://api.polygon.io"
