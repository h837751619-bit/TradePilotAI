FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
COPY scripts ./scripts
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic
COPY entrypoint.sh ./entrypoint.sh
RUN pip install --no-cache-dir fastapi pydantic-settings sqlalchemy alembic uvicorn

ENV PYTHONPATH=/app/src
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "tradepilot.main:app", "--host", "0.0.0.0", "--port", "8000"]
