FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml /app/
RUN pip install --no-cache-dir .

COPY src/ /app/src/

ENTRYPOINT ["python", "-m", "src.main"]
