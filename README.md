# Invent! Agents and R

To solve real-world problems, AI agents need to choose the correct tool to use.
The aim of this project is to engineer an ecosystem of AI agents and tools to support intuitive conversational execution of statistical functions.

The current implementation is an AI agent that can produce random numbers from various probability distributions.
It's made with industry-standard components, representing a foundation for building natural language interfaces for complex workflows.

![AI agent uses R `rbinom` function in response to "Simulate 100 coin tosses and count the number of heads."](https://chnosz.net/guest/invent/rbinom.png)

## Overview

We use [Docker Compose] to connect an [Agent Development Kit] client to an MCP server from the [mcptools] package running in an [R environment].

- Model Context Protocol (MCP) allows AI agents to interact with external tools in a client-server setup.
- Docker Compose supports definitions of containerized AI agents and one or more MCP servers (through Docker MCP Gateway) for scalable and secure deployment.
- R offers many statistical functions that can be exposed through an MCP server with the mcptools package.

"invent" was chosen as the Docker Compose project name to make it easier to find in log messages, image names, etc.

## Build and run the project (OpenAI)

Build the project:

```sh
docker compose build
```

This creates a compose **project** and three **images**:

- `docker compose ls -a`: invent
- `docker images`: invent-tools, invent-agent, docker/mcp-gateway

Next, put your OpenAI API key (`sk-proj-...`) in `secret.openai-api-key`.
Then run the project:

```sh
docker compose up
```

You can access the ADK Dev UI at <http://localhost:8080>.

The LLM used here is gpt-4o-mini.
If you want to use a different model, change it in `entrypoint.sh`.

## Run the project (local LLM)

To use a local LLM running on your GPU, install [Docker Model Runner] before running this command.

```sh
docker compose -f compose.yaml -f model-runner.yaml up
```

The LLM used here is [Gemma 3]; this can be changed in `model-runner.yaml`.

## Develop the project (in container)

With this command, changes you make to the R and Python code on the host computer are reflected in the running project.

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

- The `invent-tools` image is based on [rocker/v-ver]
  - `server.R` defines **18 tools** to generate random numbers from various probability distributions
- The `invent-agent` image is based on [Docker Python slim]
  - `random-agent/agent.py` defines an **MCPToolset** that is passed to the LLM along with instructions for using the tools
  - `random-agent/__init__.py` has code to reduce log verbosity and is modified from [docker/compose-for-agents]
- The [Docker MCP Gateway] routes requests to MCP servers (just one in our case)
  - A custom `catalog.yaml` makes our R MCP server visible to the MCP Gateway
  - For more options, see [MCP Gateway docs] and [Docker MCP Catalog] for the default `catalog.yaml`
- Specific actions are used for [Docker Watch]
  - `action: rebuild` is used for `server.R` because we need to restart the MCP server if the R code changes
  - `action: sync` is used for `random-agent` because the ADK web server supports hot reloading with the
    [`--reload_agents`](https://github.com/google/adk-python/commit/e545e5a570c1331d2ed8fda31c7244b5e0f71584) flag
  
## Examples

In these examples, the user describes the problem and the agent chooses a distribution and calls the correct tool.

- Uniform distribution

![AI agent uses R `runif` function in response to "Draw 5 random numbers between 0 and 100. Choose the distribution that is appropriate for this problem."](https://chnosz.net/guest/invent/runif.png)

- Hypergeometric distribution

![AI agent uses R `rhyper` function in response to "Draw 10 balls from a box of 20 total balls (5 red, 15 blue). Do this twice and list the number of red balls drawn in each trial."](https://chnosz.net/guest/invent/rhyper.png)

## Tool reference


The following distributions are available for generating random numbers.
See the [R help page on Distributions] for more information.

**Discrete distributions**

Binomial distribution, Poisson distribution, geometric distribution, hypergeometric distribution, multinomial distribution, negative binomial distribution

**Continuous distributions**

Normal distribution, uniform distribution, exponential distribution, chi-squared distribution, Student *t* Distribution, gamma Distribution, beta distribution, Cauchy distribution, *F* distribution, log-normal distribution, Weibull distribution

[Docker Compose]: https://docs.docker.com/compose/
[Agent Development Kit]: https://google.github.io/adk-docs/
[R environment]: https://www.r-project.org/
[mcptools]: https://github.com/posit-dev/mcptools
[Docker MCP Gateway]: https://docs.docker.com/ai/mcp-gateway/
[Docker Model Runner]: https://docs.docker.com/ai/model-runner/
[Gemma 3]: https://deepmind.google/models/gemma/gemma-3/
[MCP Gateway docs]: https://github.com/docker/mcp-gateway/blob/main/docs/mcp-gateway.md
[Docker MCP Catalog]: http://desktop.docker.com/mcp/catalog/v2/catalog.yaml
[rocker/v-ver]: https://rocker-project.org/images/versioned/r-ver
[Docker Python slim]: https://hub.docker.com/_/python/#pythonversion-slim
[docker/compose-for-agents]: https://github.com/docker/compose-for-agents
[Docker Watch]: https://docs.docker.com/compose/how-tos/file-watch/
[R help page on Distributions]: https://stat.ethz.ch/R-manual/R-devel/library/stats/html/Distributions.html
