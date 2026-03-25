FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /workspace

COPY pyproject.toml uv.lock ./
COPY packages/stocklake-tiingo ./packages/stocklake-tiingo
COPY services/datalake ./services/datalake
COPY services/market-live ./services/market-live
COPY services/mcp-stocklake ./services/mcp-stocklake

RUN uv sync --frozen --package stocklake-market-live

ENV PATH="/workspace/.venv/bin:$PATH"

WORKDIR /workspace/services/market-live

EXPOSE 8001

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
