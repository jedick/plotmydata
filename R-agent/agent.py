from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import LlmAgent
from google.genai.types import Part
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.base_tool import BaseTool
from typing import Dict, Any, Optional
from mcp import types
import base64
import os

# Define MCP connection parameters
url = os.environ["MCPGATEWAY_ENDPOINT"]

# Define model
# If we're using the OpenAI API, get the value of OPENAI_MODEL_NAME set by entrypoint.sh
# If we're using an OpenAI-compatible endpoint (Docker Model Runner), use a fake API key
model = LiteLlm(
    model=os.environ.get("OPENAI_MODEL_NAME", ""),
    api_key=os.environ.get("OPENAI_API_KEY", "fake-API-key"),
)

"""Agent for generating random numbers."""

# Filter tools for random numbers
random_filter = [
    # fmt: off
    # Discrete
    "rbinom", "rpois", "rgeom", "rhyper", "rmultinom", "rbinom",
    # Continuous
    "rnorm", "runif", "rexp", "rchisq", "rt", "rgamma", "rbeta", "rcauchy", "rf", "rlogis", "rlnorm", "rweibull",
    # fmt: on
]
# Define the McpToolset with connection parameters
random_toolset = McpToolset(
    connection_params=SseConnectionParams(url=url),
    tool_filter=random_filter,
)

random_instruction = """
You are a helpful agent who can generate random numbers from various distributions.
Only generate random numbers if the user specifies the distribution.
Otherwise, tell the user what distributions are available.

All distributions require `n`, the number of observations or random values to generate.
For the hypergeometric distribution, `nn` is the number of observations.
Additional requirements for discrete distributions are given below:

The binomial distribution requires `size` (number of trials) and `prob` (probability of success in each trial).
The Poisson distribution requires `lambda` (mean and variance).
The geometric distribution requires `prob` (probability of success in each trial).
The hypergeometric distribution requires `m` (number of white balls), `n` (number of black balls), and `k` (number of balls drawn from the urn).
The multinomial distribution requires `size` (total number of objects put into K boxes) and `prob` (vector of probabilities for the K classes).
The negative binomial distribution requires `size` (target for number of successful trials) and `prob` (probability of success in each trial).

For continuous distributions, only change the default values if requested by the user.
The default values for continuous distributions are given below:

rnorm(mean = 0, sd = 1) # `sd` is standard deviation.
runif(min = 0, max = 1) # `min` and `max` are lower and upper limits.
rexp(rate = 1) # `rate` is the rate parameter (lambda).
rchisq(ncp = 0) # `ncp` is the non-centrality parameter.
rt() # Omitted `ncp` (non-centrality parameter) for the central t distribution.
rgamma(rate = 1, scale = 1/rate) # `rate` is an alternative way to specify the scale; `scale` is the scale parameter.
rbeta(ncp = 0) # `ncp` is the non-centrality parameter.
rf() # Omitted `ncp` (non-centrality parameter) for the central F distribution.
rlogis(location = 0, scale = 1) # `location` and `scale` are location and scale parameters.
rlnorm(meanlog = 0, sdlog = 1) # `meanlog` and `sdlog` are mean and standard deviation of the distribution on the log scale.
rweibull(scale = 1) # `scale` is the scale parameter.

Additional requirements for continuous distributions are given below:

The Chi-Squared distribution requires `df` (degrees of freedom).
The Student t distribution requires `df` (degrees of freedom).
The Gamma distribution requires `shape` (shape parameter).
The Beta distribution requires `shape1` and `shape2` (shape parameters).
The Cauchy distribution requires `location` (location parameter) and `scale` (scale parameter).
The F distribution requires `df1` and `df2` (degrees of freedom).
The Weibull distribution requires `shape` (shape parameter).
"""

random_agent = LlmAgent(
    name="random_agent",
    description="Agent for generating random numbers using R functions",
    model=model,
    instruction=random_instruction,
    tools=[random_toolset],
)

"""Agent for making scatterplots."""

# Filter tools for plotting
plot_filter = ["mkplot"]
# Define the McpToolset with connection parameters
plot_toolset = McpToolset(
    connection_params=SseConnectionParams(url=url),
    tool_filter=plot_filter,
)

plot_instruction = """
You are a helpful agent who can make scatterplots.
The required values are in the `x` and `y` arguments.
The `type` argument is optional and can be used to change the plot type (points, lines, or both).
"""


# Callback function to save PNG returned from mkplot() as an ADK artifact
async def save_plot_artifact(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict
) -> Optional[Dict]:
    if tool.name == "mkplot":
        # tool_response is a CallToolResult (type from mcp)
        # https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file#parsing-tool-results
        for content in tool_response.content:
            if isinstance(content, types.TextContent):
                # Convert mkplot tool response (hex string) to bytes
                byte_data = bytes.fromhex(content.text)
                # Encode binary data to Base64 format
                encoded = base64.b64encode(byte_data).decode("utf-8")
                artifact_part = Part(
                    inline_data={
                        "data": encoded,
                        "mime_type": "image/png",
                    }
                )
                # TODO: Use unique filename
                filename = "mkplot.png"
                await tool_context.save_artifact(
                    filename=filename, artifact=artifact_part
                )
                return "Plot saved as artifact: {filename}"

    # Passthrough for other tools no matching content
    return None


plot_agent = LlmAgent(
    name="plot_agent",
    description="Agent for making scatterplots using R",
    model=model,
    instruction=plot_instruction,
    tools=[plot_toolset],
    after_tool_callback=save_plot_artifact,
)

root_description = """
I route requests to agents for generating random numbers or plotting data using R functions.
"""

root_instruction = """
You are the coordinator of a multi-agent system for running R functions based on the user's request.
Use random_agent for generating random numbers and plot_agent for plotting data.
If the user asks for capabilities or availability of functions, route the request to the appropriate agent.
If a suitable agent is not available, inform the user.
"""

# Create parent agent and assign children via sub_agents
root_agent = LlmAgent(
    name="Coordinator",
    description=root_description,
    model=model,
    instruction=root_instruction,
    sub_agents=[  # Assign sub_agents here
        random_agent,
        plot_agent,
    ],
)
