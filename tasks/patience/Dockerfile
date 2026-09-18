# patience — temporal-preference measurement. See tasks/patience/README.md.
FROM python:3.11-slim
RUN apt-get update -q && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir flask==3.0.3 numpy==2.1.3
RUN useradd -m agent
WORKDIR /app
COPY app/server.py /app/server.py
COPY app/PROBLEM.md /app/PROBLEM.md
COPY env /app/env
# State and ledger are root-only: the agent drives the console through the API but can neither read
# the carried debt (unless the condition discloses it) nor touch the ground truth estimate.py reads.
RUN mkdir -p /var/ops \
 && chown -R root:root /app && chmod 700 /app/server.py && chmod 755 /app/PROBLEM.md \
 && chmod -R go-rwx /app/env \
 && chown root:root /var/ops && chmod 700 /var/ops
CMD ["python", "/app/server.py"]
