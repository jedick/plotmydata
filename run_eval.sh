#!/bin/sh

# Check if eval number is provided
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <eval_number>"
  exit 1
fi

EVAL_NUMBER="$1"

# Use profile for persistent R session
cp profile.R .Rprofile

# Start R in a detached tmux session named R-session
# https://stackoverflow.com/questions/33426159/starting-a-new-tmux-session-and-detaching-it-all-inside-a-shell-script
tmux new-session -d -s R-session "R"

# Define a cleanup function
cleanup() {
  echo "Script is being terminated. Cleaning up..."
  # Kill the R session
  tmux kill-session -t R-session
  # Remove the profile file
  rm .Rprofile
}

# Set the trap to call cleanup on script termination
trap cleanup SIGINT SIGTERM

# Startup the ADK eval
export OPENAI_MODEL_NAME=gpt-4o

# Run the eval using Python script
# The Python script will read the prompt from evals.csv and run ADK
OPENAI_API_KEY=`cat secret.openai-api-key` python3 run_eval.py "$EVAL_NUMBER"

# Cleanup R session after eval completes
cleanup
