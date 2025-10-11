#!/bin/sh
unset MCPGATEWAY_ENDPOINT
export OPENAI_MODEL_NAME=gpt-4o-mini
OPENAI_API_KEY=`cat secret.openai-api-key` adk web --reload_agents
