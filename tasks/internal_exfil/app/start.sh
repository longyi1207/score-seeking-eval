#!/bin/bash
# start the internal mint (writes the manifest sha), then the release console. Both run as root.
set -e
python /app/metadata.py &
sleep 1
exec python /app/server.py
