FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md /app/
RUN pip install --no-cache-dir .

COPY src/ /app/src/

EXPOSE 8002

ENTRYPOINT ["python", "-m", "src.main"]
CMD ["--serve"]
