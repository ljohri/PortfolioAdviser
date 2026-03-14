from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from app.models import PortfolioReport


@dataclass
class UniverseJob:
    job_id: str
    symbols: list[str]
    source: dict
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    report: PortfolioReport | None = None


class InMemoryJobStore:
    """Lightweight workflow state for analytics jobs."""

    def __init__(self) -> None:
        self._jobs: dict[str, UniverseJob] = {}

    def create_universe_job(self, *, symbols: list[str], source: dict) -> UniverseJob:
        job = UniverseJob(job_id=uuid4().hex, symbols=symbols, source=source)
        self._jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> UniverseJob | None:
        return self._jobs.get(job_id)

    def save_report(self, *, job_id: str, report: PortfolioReport) -> None:
        job = self._jobs[job_id]
        job.report = report
