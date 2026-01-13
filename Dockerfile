# Declare the base image
FROM rocker/r-ver:latest

# Considerations for local development: reduce Docker cache size and rebuild time
#   Single RUN directive and two COPY directives
#     Pre-RUN COPY for relatively stable files, post-RUN COPY for app files
#   Avoid other directives like USER and ENV
#     startup.sh activates the virtual environment for running the app
# Considerations for remote development (HF Spaces Dev Mode)
#   Dev Mode requires useradd, chown and USER
#   Use CMD instead of ENTRYPOINT

# Set working directory and copy non-app files
WORKDIR /app
COPY requirements.txt entrypoint.sh .

# Install Python and system tools
# Create and activate virtual environment for installing packages
# Install required Python and R packages
# Rename startup script and make it executable
# Add user with uid=1000 and chown /app directory for HF Spaces Dev Mode
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv screen vim git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    python3 -m venv /opt/venv && \
    export PATH="/opt/venv/bin:$PATH" && \
    pip --no-cache-dir install -r requirements.txt && \
    R -q -e 'install.packages(c("ellmer", "mcptools", "readr", "ggplot2", "tidyverse"))' && \
    cp entrypoint.sh startup.sh && \
    chmod +x startup.sh && \
    useradd -m -u 1000 user && \
    chown -R user /app
    
# Copy app files with user permissions
# NOTE: This overwrites all copied files, rendering them non-executable. That is why we
# created an executable file with a different name (startup.sh) that is not overwritten here.
COPY --chown=user . /app

# Set the user for Dev Mode
USER user

# Set default command (executable file in WORKDIR)
CMD [ "/app/startup.sh" ]
