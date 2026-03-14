FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir .

COPY mcp_market_live /app/mcp_market_live

CMD ["python", "-m", "mcp_market_live"]
