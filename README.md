# Plot My Data - using R with AI agents

The [R software environment] is an open-source platform for statistics, data analysis and visualization.
To help R users solve real-world problems, AI agents need access to tools and guidance about their usage.

The aim of this project is to build an intuitive conversational interface to powerful plotting functions.
To do this, we are engineering an ecosystem of AI agents and tools that can run R code and make plots.

A test-driven approach to AI development using known-good traces as evaluation cases ensures that the system works as expected.
It's made with industry-standard components, supporting different models and scalable deployment options.

![Animation of a chat with an AI agent to plot histograms of sums of squares of normal random numbers](https://chnosz.net/guest/plotmydata/test-animation.gif)

Note: In this example, the agent uses the `Hide` tool to modify R variables without returning the results.
This way the LLM isn't flooded with thousands of tokens representing random numbers.

## Features

- Instant visualization: Plots are shown in the chat interface and downloadable as conversation artifacts.
- Interactive analysis: Use an R session so variables persist across tool calls.

## Running the project

There project can be run with or without a container.

<details open>
<summary><strong>Containerless</strong></summary>

This requires a local installation of R and Python with packages listed in `requirements.txt`.
Configure the model and start the ADK web server:

```sh
export OPENAI_MODEL_NAME=gpt-4o-mini
OPENAI_API_KEY=your-api-key adk web --reload_agents
```

`run.sh` is a shortcut to these commands, taking the API key from `secret.openai-api-key`.
This script also starts an R session that can be used to persist variables across tools calls.
</details>

<details>
<summary><strong>Containerized</strong></summary>

First, build the project.
This creates a `plotmydata` Docker Compose project and a `plotmydata-app` image.

```sh
docker compose build
```

Now run the project.
This uses your OpenAI API key (`sk-proj-...`) from `secret.openai-api-key`.

```sh
docker compose up
```

Press `w` to start watching file changes.
Alternatively, use this command so changes to the R and Python code on the host computer are reflected in the running project.

```sh
docker compose watch
```
</details>

<details>
<summary><strong>Changing the model</strong></summary>

The remote LLM is gpt-4o-mini.
If you want to use a different one, change it in `entrypoint.sh`.

To use a local LLM running on your GPU, install [Docker Model Runner] before running this command.

```sh
docker compose -f compose.yaml -f model-runner.yaml up
```

The local LLM is [Gemma 3]; this can be changed in `model-runner.yaml`.
</details>

## Examples

<details open>
<summary><strong>Plotting data:</strong> <i>Plot radius_worst (y) vs radius_mean (x) from https://zenodo.org/records/3608984/files/breastcancer.csv?download=1. Add a blue 1:1 line and title "Breast Cancer Wisconsin (Diagnostic)".</i></summary>

![Chat with AI agent to plot breast cancer data from a CSV file at a given URL](https://chnosz.net/guest/plotmydata/breast-cancer.png)

Note: This dataset is from the [UCI Machine Learning Repository]. The Zenodo URL is used to download a CSV version.
</details>

<details>
<summary><strong>Plotting functions:</strong> <i>Plot a Sierpiński Triangle</i></summary>

<img width="50%" alt="Chat with AI agent to plot Sierpiński Triangle" src="https://chnosz.net/guest/plotmydata/sierpinski-triangle.png" />

Note: This dataset is from the [UCI Machine Learning Repository]. The Zenodo URL is used to download a CSV version.
</details>

<details>
<summary><strong>Persist variables:</strong> <i>Use a session</i></summary>

The full prompt history:
- Use a session
- Save 100 random numbers from a normal distribution in x
- Run y = x^2
- Plot a histogram of y

![Chat with AI agent to use an R session](https://chnosz.net/guest/plotmydata/use-session.png)
</details>

## Under the hood

Model Context Protocol (MCP) allows AI agents to interact with external tools in a client-server setup.
We connect an [Agent Development Kit] client to an MCP server from the [mcptools] R package.
[Docker Compose] supports definitions of containerized AI agents and one or more MCP servers for scalable and secure deployment.

- The `plotmydata-tools` image is based on [rocker/v-ver]
  - `server.R` defines tools to run R code and make plots
- The `plotmydata-agent` image is based on [Docker Python slim]
  - `PlotMyData/agent.py` defines an **McpToolset** that is passed to the LLM along with instructions for using the tools
  - `PlotMyData/__init__.py` has code to reduce log verbosity and is modified from [docker/compose-for-agents]
- Specific actions are used for [Docker Watch]
  - `action: rebuild` is used for `server.R` because we need to restart the MCP server if the R code changes
  - `action: sync` is used for `PlotMyData` because the ADK web server supports hot reloading with the
    [`--reload_agents`](https://github.com/google/adk-python/commit/e545e5a570c1331d2ed8fda31c7244b5e0f71584) flag

[R software environment]: https://www.r-project.org/
[Docker Compose]: https://docs.docker.com/compose/
[Agent Development Kit]: https://google.github.io/adk-docs/
[mcptools]: https://github.com/posit-dev/mcptools
[Docker Model Runner]: https://docs.docker.com/ai/model-runner/
[Gemma 3]: https://deepmind.google/models/gemma/gemma-3/
[rocker/v-ver]: https://rocker-project.org/images/versioned/r-ver
[Docker Python slim]: https://hub.docker.com/_/python/#pythonversion-slim
[docker/compose-for-agents]: https://github.com/docker/compose-for-agents
[Docker Watch]: https://docs.docker.com/compose/how-tos/file-watch/
[R help page on Distributions]: https://stat.ethz.ch/R-manual/R-devel/library/stats/html/Distributions.html
[UCI Machine Learning Repository]: https://doi.org/10.24432/C5DW2B
