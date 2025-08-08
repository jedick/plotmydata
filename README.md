# Invent! Agents and R

Discover an intuitive conversational interface to powerful statistical methods.
This project uses [Docker Compose] to connect an [Agent Development Kit] client to an MCP server running in R with the [mcptools] package.
The agent can call R functions to produce random numbers from various probability distributions.

**User:** Simulate 100 coin tosses and count the number of heads.
<br>
**Agent:** [Chooses a tool for the binomal distribution and calls it with appropriate arguments.] The simulation resulted in 52 heads.

## Overview

Model Context Protocol (MCP) allows AI agents to interact with external tools in a client-server setup.
Docker Compose supports definitions of containerized AI agents and one or more MCP servers (through Docker MCP Gateway) as a foundation for scalable and secure deployment.
R offers many statistical functions that can be exposed through an MCP server with the mcptools package.

"invent" was chosen as the Docker Compose project name to make it easier to find in log messages, image names, etc.

## Build and run the project (OpenAI)

To use gpt-4o-mini as the LLM, put your OpenAI API key (`sk-proj-...`) in `secret.openai-api-key`, then run this command.

```sh
docker compose build
```

This creates a compose **project** and three **images**:

- `docker compose ls -a`: invent
- `docker images`: invent-tools, invent-agent, docker/mcp-gateway

Now it's time to run the project!

```sh
docker compose up
```

You can access the ADK Dev UI at <http://localhost:8080>.

In case you want to use a different model, change it in `entrypoint.sh`.

## Run the project (local LLM)

To use a local LLM running on your GPU, install [Docker Model Runner] before running this command.

```sh
docker compose -f compose.yaml -f model-runner.yaml up
```

The LLM used here is [Gemma 3]; this can be changed in `model-runner.yaml`.

## Develop the project (in container)

With this command, changes you make to the Python code on the host computer are immediately reflected in the running project.

```sh
docker compose watch
```

Alternatively, start the project with one of the previous commands and press `w` to start watching file changes.

## Develop the project (on host system)

Make sure to install the packages listed in `requirements.txt`.

Start the MCP Gateway:

```sh
docker mcp gateway run --catalog=./catalog.yaml --servers=r-mcp --transport=sse --port=8811
```

Start the ADK web UI:

```sh
export MCPGATEWAY_ENDPOINT=http://127.0.0.1:8811
export OPENAI_MODEL_NAME=gpt-4o-mini
OPENAI_API_KEY=your-api-key adk web --reload_agents
```

## Under the hood

- `server.R` defines **18 tools** to generate random numbers from various probability distributions
- The structure of the `random-agent` directory follows [ADK Quickstart]
  - `agent.py` defines an **MCPToolset** that is passed to the LLM along with instructions for using the tools
  - `__init__.py` has code to reduce log verbosity and is modified from [docker/compose-for-agents]
- The [Docker MCP Gateway] routes requests to MCP servers (just one in our case)
  - A custom `catalog.yaml` makes our R MCP server visible to the MCP Gateway
  - For more options, see [MCP Gateway docs] and [Docker MCP Catalog] for the default `catalog.yaml`
- Specific actions are used for [Docker Watch]:
  - `action: rebuild` is used for `server.R` because we need to restart the MCP server if the R code changes
  - `action: sync` is used for `random-agent` because the ADK web server supports hot reloading with the `[--reload_agents]` flag
  
## Examples

- What distributions are available?
- Draw 10 random numbers between 0 and 1
- Simulate 100 coin tosses and count the number of heads
- Simulate this scenario: Draw 10 balls from a box of 20 total balls (7 red, 13 blue) and count the red balls drawn
- Imagine a scenario using the log-normal distribution and run the code to execute it

[Docker Compose]: https://docs.docker.com/compose/
[Agent Development Kit]: https://google.github.io/adk-docs/
[mcptools]: https://github.com/posit-dev/mcptools
[Docker MCP Gateway]: https://docs.docker.com/ai/mcp-gateway/
[Docker Model Runner]: https://docs.docker.com/ai/model-runner/
[Gemma 3]: https://deepmind.google/models/gemma/gemma-3/
[MCP Gateway docs]: https://github.com/docker/mcp-gateway/blob/main/docs/mcp-gateway.md
[Docker MCP Catalog]: http://desktop.docker.com/mcp/catalog/v2/catalog.yaml
[ADK Quickstart]: https://google.github.io/adk-docs/get-started/quickstart/
[docker/compose-for-agents]: https://github.com/docker/compose-for-agents
[Docker Watch]: https://docs.docker.com/compose/how-tos/file-watch/
[--reload_agents]: https://github.com/google/adk-python/commit/e545e5a570c1331d2ed8fda31c7244b5e0f71584
