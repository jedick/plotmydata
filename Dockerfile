## Image 1: R environment with MCP server

# Base image with development version of R
FROM rocker/r-ver AS r-ver

# Install R packages
RUN R -q -e 'install.packages(c("ellmer", "mcptools", "readr", "ggplot2"))'

# Copy the project files
COPY server.R prompts.R .

# Run the MCP server
CMD ["Rscript", "server.R"]

## Image 2: Python environment with ADK
## Modified from: https://github.com/docker/compose-for-agents/tree/main/adk

# Base image with Python
FROM python:3.13-slim AS adk
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source files and compile to bytecode
COPY prompts.py .
COPY PlotMyData PlotMyData
RUN python -m compileall -q .

# Copy startup script
COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

ENTRYPOINT [ "/entrypoint.sh" ]
