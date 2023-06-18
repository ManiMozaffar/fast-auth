FROM python:3.11.3

WORKDIR /src

COPY pyproject.toml poetry.lock* ./

RUN pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY . .

ENV PYTHONPATH=/app:$PYTHONPATH

EXPOSE 9990

CMD ["make", "deploy"]
