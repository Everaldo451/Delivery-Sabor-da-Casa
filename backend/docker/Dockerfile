FROM python:latest

WORKDIR /app

ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"

RUN pip install --no-cache-dir uv==0.13.6

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
