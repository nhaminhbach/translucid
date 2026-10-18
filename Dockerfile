FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md ./
COPY translucid ./translucid
COPY configs ./configs
COPY data ./data

RUN uv pip install --system -e ".[web]"

ENV PORT=8080
EXPOSE 8080

CMD ["python", "-m", "translucid.eval.benchmark"]
