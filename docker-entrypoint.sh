#!/bin/sh
set -eu
# Railway mounts volumes as root; only the dedicated app-data directory changes owner.
mkdir -p "${STUDIO_DATA_DIR:-/data}"
chown studio:studio "${STUDIO_DATA_DIR:-/data}"
exec gosu studio "$@"
