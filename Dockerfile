FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && apt-get install -y git && apt-get clean

ADD . /app

WORKDIR /app

RUN uv sync --locked
RUN uv pip install 'git+https://<GITHUB_TOKEN>@github.com/RFHamster/nuvie-db.git'

EXPOSE 6543

ENTRYPOINT ["./scripts/entrypoint.sh"]
