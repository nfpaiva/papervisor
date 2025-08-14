#!/usr/bin/env bash
set -euo pipefail
xenon --max-absolute E --max-modules C --max-average B \
  --exclude "src/papervisor/cli.py,src/papervisor/web_server.py" \
  src
