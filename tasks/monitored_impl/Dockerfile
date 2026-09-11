FROM python:3.11-slim

# non-root agent; the task has no in-container secret (held-out grader is piped in at grade time,
# the monitor runs outside), so this is just hygiene / consistency with the other tasks.
RUN useradd -m -u 1000 agent
WORKDIR /app
COPY app /app
RUN chown -R agent:agent /app
CMD ["sleep", "infinity"]
