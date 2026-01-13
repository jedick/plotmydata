# Plot My Data - using R with AI agents

[![Open in HF Spaces](https://huggingface.co/datasets/huggingface/badges/resolve/main/open-in-hf-spaces-sm.svg)](https://huggingface.co/spaces/jedick/plotmydata)

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

- Multiple data sources: Upload a file, provide a URL, or use built-in [R datasets]
- Data awareness: Uploaded files are automatically summarized for the LLM
  - *This lets you describe a plot without knowing the exact variable names*
- Code generation: The LLM writes R code based on its internal knowledge
- Code execution: Tools are provided for making plots with base [R graphics] (default) and [ggplot2]
  - *To use ggplot2, just mention "ggplot" or "ggplot2" in your message*
- Instant visualization: Plots are shown in the chat interface and downloadable as artifacts
- Interactive analysis: The agent uses an R session so the environment persists across chat messages and tool calls

## Running the app

The app can be run with or without a container.

<details open>
<summary><strong>Containerless</strong></summary>

- Install R and run `install.packages(c("ellmer", "mcptools", "readr", "ggplot2", "tidyverse"))`
- Install Python with packages listed in `requirements.txt`
- Put your OpenAI API key in a file named `secret.openai-api-key`
- Execute `run_web.sh` to start an R session and launch the ADK web UI

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
<summary><strong>Plot data:</strong> <i>Plot radius_worst (y) vs radius_mean (x) from https://github.com/jedick/plotmydata/raw/refs/heads/main/evals/data/breast-cancer.csv. Add a blue 1:1 line and title "Breast Cancer Wisconsin (Diagnostic)".</i></summary>

![Plot of breast cancer data created by an AI agent instructed to use a CSV file at a given URL](https://chnosz.net/guest/plotmydata/breast-cancer.png)

</details>

<details>
<summary><strong>Plot functions:</strong> <i>Plot a Sierpiński Triangle</i></summary>

<img width="50%" alt="Chat with AI agent to plot Sierpiński Triangle" src="https://chnosz.net/guest/plotmydata/sierpinski-triangle.png" />

</details>

<details>
<summary><strong>Interactive analysis:</strong> [click to open] </summary>

- *Save 100 random numbers from a normal distribution in x*
- *Run y = x^2*
- *Plot a histogram of y*

![Histogram of squared normal random numbers created with an AI agent using R session](https://chnosz.net/guest/plotmydata/use-session.png)
</details>

## Evals

Accuracy = fraction of correct plots.
**Plot correctness is currently judged by a human.**

| Eval set | Size | Prompt set | Accuracy | Notes |
|-|-|-|-|-|
| 01 | 27 | [bb4eead] | 0.41 | Mainly base graphics: barplot, boxplot, cdplot, coplot, contour, dotchart, filled.contour, grid
| 01 | 27 | [e9180aa] | 0.52 | Add help tools to get R documentation
| 02 | 37 | [e9180aa] | 0.49 | More base graphics: hist, image, lines, matplot, mosaicplot, pairs, rug, spineplot, plot.window
| 03 | 40 | [30c22a1] | 0.50 | Handle uploaded CSV files
| 03 | 40 | [b8e5f8c] | 0.38 | Add agent for loading and summarizing data

<details>
<summary>Evals management</summary>

The repo tracks both evaluation sets and prompt sets.
For example, the `evals/01` directory contains all results for the first evaluation set using different prompt sets.
The file name uses the short commit hash for the prompt set used for evaluation.

Each eval consists of a query and reference code and image.
Because of their size, reference and generated images are not stored in this repo.

To run evals, copy the latest eval CSV file to `evals/evals.csv`.
Then use e.g. `run_eval.sh 1` to run the first eval.
This script: 1) saves the tool calls, generated code, and current date to the CSV file and 2) saves the generated image to the `evals/generated` directory.

After running evals, change to the `evals` directory and run `streamlit run edit_evals.py` to edit the eval CSV file.
This app allows:
- Choosing an eval to edit
- Viewing the reference and generated images side-by-side
- Indicating whether the generated plot is correct (True or False)
- Editing other eval data (e.g. query, file name for data upload, reference code, notes)
- Adding new evals

</details>

## Under the hood

- Model Context Protocol (MCP) allows AI agents to interact with external tools in a client-server setup
- We connect an [Agent Development Kit] client to an MCP server from the [mcptools] R package
- For access from R, file uploads are saved as artifacts using an [ADK plugin], then as temporary files using a callback function
- `PlotMyData/__init__.py` has code to reduce log verbosity and is modified from [docker/compose-for-agents]

Container notes:

- The Docker image is based on [rocker/r-ver] and adds R packages and a Python installation
- [Docker Compose] is used for port mapping, secrets, and watching file changes with [Docker Watch]
- The ADK web UI is run with the [`--reload_agents`] flag so that changes to `agent.py` on the host system are reflected in the running container

## Licenses

- This code in repo is licensed under MIT
- Some examples used in evals are taken from R and are licensed under GPL-2|GPL-3
- `breast-cancer.csv` (the CSV version from [Kaggle]) is licensed under CC0;
  the original dataset (from the [UCI Machine Learning Repository]) is licensed under CC BY 4.0

[R software environment]: https://www.r-project.org/
[R datasets]: https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/00Index.html
[R graphics]: https://stat.ethz.ch/R-manual/R-devel/library/graphics/html/00Index.html
[ggplot2]: https://ggplot2.tidyverse.org/
[Agent Development Kit]: https://google.github.io/adk-docs/
[mcptools]: https://github.com/posit-dev/mcptools
[Docker Model Runner]: https://docs.docker.com/ai/model-runner/
[Gemma 3]: https://deepmind.google/models/gemma/gemma-3/
[docker/compose-for-agents]: https://github.com/docker/compose-for-agents
[ADK plugin]: https://medium.com/google-cloud/2-minute-adk-manage-context-efficiently-with-artifacts-6fcc6683d274
[rocker/r-ver]: https://rocker-project.org/images/versioned/r-ver
[Docker Compose]: https://docs.docker.com/compose/
[Docker Watch]: https://docs.docker.com/compose/how-tos/file-watch/
[`--reload_agents`]: https://github.com/google/adk-python/commit/e545e5a570c1331d2ed8fda31c7244b5e0f71584
[UCI Machine Learning Repository]: https://doi.org/10.24432/C5DW2B
[Kaggle]: https://www.kaggle.com/datasets/yasserh/breast-cancer-dataset

[bb4eead]: https://github.com/jedick/plotmydata/commit/bb4eead2346d936f9c83108b16f20faf3e3c522c
[e9180aa]: https://github.com/jedick/plotmydata/commit/e9180aa363195fd2cc011e11e4febc0f544f7878
[30c22a1]: https://github.com/jedick/plotmydata/commit/30c22a166a237bfe26413b6c28278a6c467a65a7
[b8e5f8c]: https://github.com/jedick/plotmydata/commit/b8e5f8ce5e03360b9bde26ff32acb7180d969694

