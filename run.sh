#!/bin/sh

# Run mcp_session() when R starts up to make the session available to the mcptools server
# NOTE: mcp_session() needs to be run in an *interactive* R session, so we can't put it in server.R
echo "source('summarize.R'); mcptools::mcp_session()" > .Rprofile
# Start R in a detached tmux session named R-session
# https://stackoverflow.com/questions/33426159/starting-a-new-tmux-session-and-detaching-it-all-inside-a-shell-script
tmux new-session -d -s R-session "R"

# Define a cleanup function
cleanup() {
  echo "Script is being terminated. Cleaning up..."
  # Kill the R session
  tmux kill-session -t R-session
}

# Set the trap to call cleanup on script termination
trap cleanup SIGINT SIGTERM

# Startup the ADK web UI
#export OPENAI_MODEL_NAME=gpt-4o
export OPENAI_MODEL_NAME=gpt-4o-mini
OPENAI_API_KEY=`cat secret.openai-api-key` adk web --reload_agents

