#!/bin/sh

# Exit immediately on errors
set -e

# Use profile for persistent R session
cp profile.R .Rprofile

# Start R in a detached screen session
# TODO: Look at using supervisord for another way to run multiple services
# https://docs.docker.com/engine/containers/multi-service_container/#use-a-process-manager
screen -d -m R

# Activate virtual environment
export PATH="/opt/venv/bin:$PATH"

# Set OpenAI model
export OPENAI_MODEL_NAME=gpt-4o
echo "Using OpenAI with ${OPENAI_MODEL_NAME}"

# Suppress e.g. UserWarning: [EXPERIMENTAL] BaseAuthenticatedTool: This feature is experimental ...
# https://github.com/google/adk-python/commit/4afc9b2f33d63381583cea328f97c02213611529
export ADK_SUPPRESS_EXPERIMENTAL_FEATURE_WARNINGS=true

# For local development, the API key is read from a file
# (not needed on HF Spaces, where secrets are injected into container's environment)
if [ -z "$OPENAI_API_KEY" ]; then
  export OPENAI_API_KEY=$(cat /run/secrets/openai-api-key)
fi

exec adk web --host 0.0.0.0 --port 8080 --reload_agents
