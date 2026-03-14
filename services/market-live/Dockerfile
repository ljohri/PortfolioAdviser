FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir . uvicorn

COPY app /app/app

EXPOSE 8001

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
