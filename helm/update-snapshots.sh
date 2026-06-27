#!/bin/bash

export SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

exec "$SCRIPT_DIR/../fugit/scripts/helm-update-snapshots.sh" "$@"
