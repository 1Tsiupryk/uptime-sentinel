FROM python:3.13 AS builder

WORKDIR /app

RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    pip install -r requirements.txt

COPY . .

FROM python:3.13-slim

ENV PATH="/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup --no-create-home appuser

WORKDIR /app

COPY --from=builder /venv /venv
COPY --from=builder --chown=appuser:appgroup /app /app

USER appuser

EXPOSE 8000

CMD ["/venv/bin/python3", "-m", "uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8000"]