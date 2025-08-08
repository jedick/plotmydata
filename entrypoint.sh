#!/bin/sh
set -e

if test -f /run/secrets/openai-api-key; then
    export OPENAI_MODEL_NAME=gpt-4o-mini
    export OPENAI_API_KEY=$(cat /run/secrets/openai-api-key)
    echo "Using OpenAI with ${OPENAI_MODEL_NAME}"
else
    export OPENAI_BASE_URL=${MODEL_RUNNER_URL}
    # Put openai/ in front of your model name, so litellm knows you're trying to call an openai /chat/completions endpoint
    # https://docs.litellm.ai/docs/providers/openai_compatible
    export OPENAI_MODEL_NAME=openai/${MODEL_RUNNER_MODEL}
    echo "Using Docker Model Runner with ${MODEL_RUNNER_MODEL}"
fi

exec adk web --host 0.0.0.0 --port 8080 --reload_agents
