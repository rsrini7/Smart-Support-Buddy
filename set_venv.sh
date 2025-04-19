#!/usr/bin/env bash

# This script activates the Python virtual environment for the backend
# Compatible with both bash and zsh
# Must be sourced: source ./set_venv.sh or . ./set_venv.sh

# Check if the script is being sourced
(return 0 2>/dev/null) || {
  echo "[ERROR] This script must be sourced: use 'source ./set_venv.sh' or '. ./set_venv.sh'"
  exit 1
}

VENV_ACTUATE_PATH="$(dirname "$0")/backend/.venv/bin/activate"

if [ -f "$VENV_ACTUATE_PATH" ]; then
  echo "Activating backend virtual environment..."
  # shellcheck disable=SC1090
  if [ -n "$ZSH_VERSION" ]; then
    source "$VENV_ACTUATE_PATH"
  elif [ -n "$BASH_VERSION" ]; then
    source "$VENV_ACTUATE_PATH"
  else
    # POSIX fallback
    . "$VENV_ACTUATE_PATH"
  fi
else
  echo "Virtual environment not found at $VENV_ACTUATE_PATH"
  return 1
fi
