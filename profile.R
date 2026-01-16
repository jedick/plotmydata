# Set a default CRAN mirror
options(repos = c(CRAN = "https://cloud.r-project.org"))

# Load a commonly used package
library(tidyverse)

# Use our own data summary function
source("data_summary.R")

# Make this R session visible to the mcptools MCP server
# NOTE: mcp_session() needs to be run in an *interactive* R session, so we can't put it in server.R
mcptools::mcp_session()
