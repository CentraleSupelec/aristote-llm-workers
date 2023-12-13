#!/bin/bash

# Exit if a command fails
set -euo pipefail

exec python -m server.app
