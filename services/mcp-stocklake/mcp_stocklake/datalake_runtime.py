from __future__ import annotations

import os
import sys
from pathlib import Path


def bootstrap_datalake_path() -> Path:
    """
    Ensure the datalake service package is importable at runtime.

    Returns:
        The resolved path to the `services/datalake` directory.
    """
    configured = os.getenv("DATALAKE_SERVICE_PATH")
    if configured:
        datalake_path = Path(configured).expanduser().resolve()
    else:
        datalake_path = Path(__file__).resolve().parents[2] / "datalake"

    path_value = str(datalake_path)
    if path_value not in sys.path:
        sys.path.insert(0, path_value)

    return datalake_path

