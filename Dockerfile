FROM python:3.13-slim AS builder
WORKDIR /app

COPY requirements.txt .

RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.13-slim
WORKDIR /app

RUN groupadd --system app && \
    useradd --system --gid app --home-dir /app --no-create-home app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --chown=app:app . .
COPY --chown=app:app ./examples/docker ./code

RUN echo "/app" > /opt/venv/lib/python3.13/site-packages/bclib.pth && \
    echo "/app/bclib" >> /opt/venv/lib/python3.13/site-packages/bclib.pth && \
    chown app:app /app

USER app

EXPOSE 9181

CMD ["python", "code/main.py"]
