from __future__ import annotations

from typing import Protocol


class TiingoSettings(Protocol):
    """Minimal settings surface required by TiingoClient."""

    tiingo_api_token: str | None
    tiingo_base_url: str
