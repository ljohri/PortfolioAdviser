from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models import ScreenRequest, ValidateRequest
from app.presets import get_presets
from app.services.engine import ScreenerEngine


@dataclass(frozen=True)
class ScreenerMcpTools:
    engine: ScreenerEngine

    def validate_screen(self, payload: dict[str, Any]) -> dict[str, Any]:
        if "source" in payload or "symbols" in payload:
            request = self.engine.parse_criteria(payload)
        else:
            validated = ValidateRequest.model_validate(payload)
            request = ScreenRequest.model_validate(
                {
                    "symbols": [],
                    "source": {"mode": "canonical_tables"},
                    "start_date": validated.start_date,
                    "end_date": validated.end_date,
                    "rules": validated.rules.model_dump(mode="json"),
                }
            )
        return self.engine.validate_criteria(request).model_dump(mode="json")

    def run_screen(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = ScreenRequest.model_validate(payload)
        return self.engine.run(request).model_dump(mode="json")

    def list_presets(self) -> list[dict[str, Any]]:
        return [preset.model_dump(mode="json") for preset in get_presets()]
