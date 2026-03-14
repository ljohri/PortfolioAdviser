from __future__ import annotations

import os
import sys


def runtime_environment_warnings() -> list[str]:
    """
    Build non-fatal startup warnings for missing environment configuration.

    Returns:
        Human-readable warning messages for runtime configuration issues.
    """
    warnings: list[str] = []
    if not os.getenv("DATABASE_URL"):
        warnings.append(
            "DATABASE_URL is not set; datalake default will be used "
            "(postgresql+psycopg://stocklake:stocklake@localhost:5432/stocklake)."
        )

    if not os.getenv("TIINGO_API_TOKEN"):
        warnings.append(
            "TIINGO_API_TOKEN is not set; live backfill calls can fail against Tiingo API."
        )

    return warnings


def emit_runtime_warnings() -> None:
    """
    Print non-fatal environment warnings to stderr before server startup.
    """
    for warning in runtime_environment_warnings():
        print(f"[mcp-stocklake][env-warning] {warning}", file=sys.stderr)

