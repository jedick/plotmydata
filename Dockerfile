# Use the rocker/r-ver image as the base
FROM rocker/r-ver:latest

# This Dockerfile is optimized to balance cache size and (re)build time
#   Single WORKDIR and RUN directives
#   Minimum number of COPY directives
#     Pre-RUN for relatively stable files: requirements.txt and entrypoint.sh
#     Post-RUN for frequently changing app files / app directory
#   Avoid other directives like USER and ENV
#     entrypoint.sh activates the virtual environment for running the app

# Set working directory and copy files
WORKDIR /app
COPY requirements.txt entrypoint.sh .

# Install Python and other necessary tools
# Create and activate virtual environment for installing packages
# Install required Python and R packages
# Make startup script executable
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv screen \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/venv \
    && export PATH="/opt/venv/bin:$PATH" \
    && pip --no-cache-dir install -r requirements.txt \
    && R -q -e 'install.packages(c("ellmer", "mcptools", "readr", "ggplot2", "tidyverse"))' \
    && chmod +x entrypoint.sh

# Copy app files
COPY prompts.py prompts.R data_summary.R server.R .

# Copy app directory
COPY PlotMyData PlotMyData

# Set entrypoint
ENTRYPOINT [ "/app/entrypoint.sh" ]
