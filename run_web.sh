#!/bin/sh

# Use profile for persistent R session
cp profile.R .Rprofile

# Start R in a detached tmux session named R-session
# https://stackoverflow.com/questions/33426159/starting-a-new-tmux-session-and-detaching-it-all-inside-a-shell-script
#tmux new-session -d -s R-session "R"

# mcptools socket isn't visible in Docker container with tmux; use screen instead
screen -d -m -S R-session R

# Define a cleanup function
cleanup() {
  echo "Script is being terminated. Cleaning up..."
  # Kill the R session
  #tmux kill-session -t R-session
  screen -X -S R-session quit
  # Remove the profile file
  rm .Rprofile
}

# Set the trap to call cleanup on script termination
trap cleanup SIGINT SIGTERM

# Startup the ADK web UI
export OPENAI_MODEL_NAME=gpt-4o
OPENAI_API_KEY=`cat secret.openai-api-key` adk web --reload_agents --log_level=WARNING

