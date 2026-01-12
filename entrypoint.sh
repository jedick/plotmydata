#!/bin/sh

# Exit immediately on errors
set -e

# MCP session setup for persistent R environment
# Create .Rprofile to run mcp_session() when R starts
echo "library(tidyverse); source('data_summary.R'); mcptools::mcp_session()" > .Rprofile

# Start R in a detached screen session
# TODO: Look at using supervisord for another way to run multiple services
# https://docs.docker.com/engine/containers/multi-service_container/#use-a-process-manager
screen -d -m R

# Activate virtual environment
export PATH="/opt/venv/bin:$PATH"

# Check for OpenAI API key
if test -f /run/secrets/openai-api-key; then
    export OPENAI_MODEL_NAME=gpt-4o
    export OPENAI_API_KEY=$(cat /run/secrets/openai-api-key)
    echo "Using OpenAI with ${OPENAI_MODEL_NAME}"
else
    # No API key, so we're using a local model
    export OPENAI_BASE_URL=${MODEL_RUNNER_URL}
    # Put openai/ in front of model name so litellm calls an openai /chat/completions endpoint
    # https://docs.litellm.ai/docs/providers/openai_compatible
    export OPENAI_MODEL_NAME=openai/${MODEL_RUNNER_MODEL}
    echo "Using Docker Model Runner with ${MODEL_RUNNER_MODEL}"
fi

exec adk web --host 0.0.0.0 --port 8080 --reload_agents
