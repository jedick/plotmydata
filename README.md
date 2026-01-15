# PlotMyData

[![Open in HF Spaces](https://huggingface.co/datasets/huggingface/badges/resolve/main/open-in-hf-spaces-lg-dark.svg)](https://huggingface.co/spaces/jedick/plotmydata)

PlotMyData is an agentic data analysis and visualization system.
It follows your prompts to drive an [R] session.

You can start with example datasets, upload your own data, or download data from a URL (currently CSV files are supported).
If you want to ask about the data or transform it before plotting, just say what you want to do.

![Animation of using PlotMyData to plot, download, upload, and explore data](https://chnosz.net/guest/plotmydata/animation-2.gif)

## Features

- Multiple data sources: Upload a file, provide a URL, or use built-in [R datasets]
- Data awareness: Data files are automatically summarized for the LLM
  - *This lets you describe a plot without knowing the exact variable names*
- Code generation: The LLM writes R code based on its internal knowledge
- Code execution: Tools are provided for making plots with base [R graphics] (default) and [ggplot2]
  - *To use ggplot2, just mention "ggplot" or "ggplot2" in your message*
- Instant visualization: Plots are shown in the chat interface and downloadable as PNG files
- Interactive analysis: The agent uses an R session so variables persist across invocations

## Running the application

The application can be run with or without a container.

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

</details>

<details>
<summary><strong>Changing the model</strong></summary>

If you want to change the remote LLM from the default (gpt-4o), change it in the startup script (`run_web.sh` or `entrypoint.sh`).

To use a local LLM, install [Docker Model Runner] then run this command.

```sh
docker compose -f compose.yaml -f model-runner.yaml up
```

See `model-runner.yaml` to change the local LLM used.
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
<summary>Evals info</summary>

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

## Architecture

- An [Agent Development Kit] client is connected to an MCP server from the [mcptools] R package
- The startup scripts launch a persistent R session with some preloaded packages and helper functions
- Data files are saved in a temporary directory using ADK's artifacts and callbacks
  - This is how the R session can access the files

Container notes:

- The Docker image is based on [rocker/r-ver] and adds R packages and a Python installation
- [Docker Compose] is used for port mapping, secrets, and watching file changes with [Docker Watch]

## Licenses

- This code in repo is licensed under MIT
- Some examples used in evals are taken from R and are licensed under GPL-2|GPL-3
- `breast-cancer.csv` (the CSV version from [Kaggle]) is licensed under CC0;
  the original dataset (from the [UCI Machine Learning Repository]) is licensed under CC BY 4.0

[R]: https://www.r-project.org/
[R datasets]: https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/00Index.html
[R graphics]: https://stat.ethz.ch/R-manual/R-devel/library/graphics/html/00Index.html
[ggplot2]: https://ggplot2.tidyverse.org/
[Agent Development Kit]: https://google.github.io/adk-docs/
[mcptools]: https://github.com/posit-dev/mcptools
[Docker Model Runner]: https://docs.docker.com/ai/model-runner/
[docker/compose-for-agents]: https://github.com/docker/compose-for-agents
[rocker/r-ver]: https://rocker-project.org/images/versioned/r-ver
[Docker Compose]: https://docs.docker.com/compose/
[Docker Watch]: https://docs.docker.com/compose/how-tos/file-watch/
[UCI Machine Learning Repository]: https://doi.org/10.24432/C5DW2B
[Kaggle]: https://www.kaggle.com/datasets/yasserh/breast-cancer-dataset

[bb4eead]: https://github.com/jedick/plotmydata/commit/bb4eead2346d936f9c83108b16f20faf3e3c522c
[e9180aa]: https://github.com/jedick/plotmydata/commit/e9180aa363195fd2cc011e11e4febc0f544f7878
[30c22a1]: https://github.com/jedick/plotmydata/commit/30c22a166a237bfe26413b6c28278a6c467a65a7
[b8e5f8c]: https://github.com/jedick/plotmydata/commit/b8e5f8ce5e03360b9bde26ff32acb7180d969694

