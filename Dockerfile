FROM python:3.10-bullseye

RUN apt-get update
RUN apt-get install upx-ucl -y

RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b /bin

WORKDIR /twittaloader

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV POETRY_VERSION 1.1.13

RUN pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock ./

RUN poetry export --dev --without-hashes -f requirements.txt | pip install --no-cache-dir -r /dev/stdin

ENTRYPOINT [ "/bin/task", "build" ]
