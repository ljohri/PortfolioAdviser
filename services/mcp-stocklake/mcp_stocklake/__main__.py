from __future__ import annotations

from contextlib import suppress

from mcp_stocklake.env_checks import emit_runtime_warnings
from mcp_stocklake.server import server


def main() -> None:
    """Run the stocklake MCP server over stdio transport."""
    # Load root .env when available so local runs and Docker share the same config contract.
    with suppress(Exception):
        from dotenv import load_dotenv

        load_dotenv()

    emit_runtime_warnings()
    server.run()


if __name__ == "__main__":
    main()

