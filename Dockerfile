FROM python:3.13-slim AS builder
WORKDIR /app

COPY requirements.txt .

RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.13-slim
WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY . .
COPY ./test/DockerSample ./code

RUN echo "/app" > /opt/venv/lib/python3.13/site-packages/bclib.pth && \
    echo "/app/bclib" >> /opt/venv/lib/python3.13/site-packages/bclib.pth


CMD ["python", "code/main.py"]
