from __future__ import annotations

from app.services.impl.backfill_logic import BackfillServiceImpl


class BackfillService:
    """Thin facade delegating backfill details to impl module."""

    def __init__(self, impl: BackfillServiceImpl) -> None:
        self._impl = impl

    async def backfill(self, **kwargs):
        return await self._impl.backfill(**kwargs)
