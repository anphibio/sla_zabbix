FROM python:3.12.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend

WORKDIR /app/backend

# The repository does not expose a Python dependency manifest yet,
# so we install the minimum runtime stack explicitly with pinned versions.
RUN pip install --no-cache-dir \
    fastapi==0.136.3 \
    "uvicorn[standard]==0.49.0" \
    sqlalchemy==2.0.50 \
    pydantic==2.13.4 \
    "psycopg[binary]==3.3.4"

COPY backend /app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
