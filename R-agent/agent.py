from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.base_tool import BaseTool
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import LlmAgent
from google.genai.types import Part
from mcp import types, StdioServerParameters
from typing import Dict, Any, Optional
import base64
import os

# Define MCP connection parameters
try:
    # This environment variable will be defined for a Docker deployment
    url = os.environ["MCPGATEWAY_ENDPOINT"]
    connection_params = SseConnectionParams(url=url)
except:
    # Fully local deployment: use stdio
    connection_params = StdioConnectionParams(
        server_params=StdioServerParameters(
            command="Rscript",
            args=[
                "server.R",
            ],
        )
    )

# Define model
# If we're using the OpenAI API, get the value of OPENAI_MODEL_NAME set by entrypoint.sh
# If we're using an OpenAI-compatible endpoint (Docker Model Runner), use a fake API key
model = LiteLlm(
    model=os.environ.get("OPENAI_MODEL_NAME", ""),
    api_key=os.environ.get("OPENAI_API_KEY", "fake-API-key"),
)

"""Agent for generating random numbers."""

# List tools for random numbers
random_tools = ["Discrete", "Continuous"]
# Define the McpToolset with connection parameters
random_toolset = McpToolset(
    connection_params=connection_params,
    tool_filter=random_tools,
)

random_instruction = """
You are a helpful agent who can generate random numbers from various distributions.
Only generate random numbers if the user specifies the distribution.
Otherwise, tell the user what distributions are available.

The available discrete distributions are binomial, Poisson, geometric, hypergeometric, multinomial, and negative binomial.

All distributions require `n`, the number of observations or random values to generate.
To use a discrete distribution, call the `Discrete` tool with the following required arguments for each distribution:
- Discrete("rbinom", n, size_binom, prob)  # binomial
- Discrete("rpois",  n, lambda)  # Poisson
- Discrete("rgeom",  n, prob)  # geometric
- Discrete("rhyper", n, m_balls, n_balls, k_balls)  # hypergeometric
- Discrete("rmultinom", n, size_multinom, prob_multinom)  # multinomial
- Discrete("rnbinom", n, size_nbinom, prob, mu)  # negative binomial

The available continuous distributions are normal, uniform, exponential, Chi-Squared, Student t, Gamma, Beta, Cauchy, F, logistic, log normal, and Weibull.

All distributions require `n`, the number of observations or random values to generate.
To use a continuous distribution, call the `Continuous` tool with the function name and required arguments.
Only change the default values if requested by the user:
- Continuous("rnorm", n, mean=0, sd=1) # normal; `sd` is standard deviation
- Continuous("runif", n, min=0, max=1) # uniform; `min` and `max` are lower and upper limits
- Continuous("rexp", n, rate=1) # exponential; `rate` is the rate parameter (lambda)
- Continuous("rchisq", n, df, ncp=0) # Chi-Squared; `ncp` is the non-centrality parameter; `df` (degrees of freedom) is required
- Continuous("rt", n, df) # Student t; omit `ncp_t` to use the central t distribution; `df` is required
- Continuous("rgamma", n, shape, scale = 1) # gamma; `scale` is the scale parameter; `shape` (shape parameter) is required
- Continuous("rbeta", n, shape1, shape2, ncp = 0) # beta; `shape1` and `shape2` are required
- Continuous("rcauchy", n, location = 0, scale = 1) # Cauchy; `location` is the location parameter
- Continuous("rf", n, df1, df2) # F; omit `ncp_f` to use the central F distribution; `df1` and `df2` are required
- Continuous("rlogis", n, location = 0, scale = 1) # logistic
- Continuous("rlnorm", n, meanlog = 0, sdlog = 1) # log normal; `meanlog` and `sdlog` are mean and standard deviation on the log scale
- Continuous("rweibull", n, shape, scale = 1) # Weibull; `shape` is required
"""

random_agent = LlmAgent(
    name="Random",
    description="Agent for generating random numbers using R functions",
    model=model,
    instruction=random_instruction,
    tools=[random_toolset],
)

"""Agent for making scatterplots."""

# List tools for plotting
plot_tools = ["BasePlot"]
# Define the McpToolset with connection parameters
plot_toolset = McpToolset(
    connection_params=connection_params,
    tool_filter=plot_tools,
)

plot_instruction = """
You are a helpful agent who can make scatterplots.
The required values are in the `x` and `y` arguments.
The `type` argument is optional and can be used to change the plot type (points, lines, or both).
"""


# Callback function to save PNG returned from BasePlot() as an ADK artifact
async def save_plot_artifact(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict
) -> Optional[Dict]:
    if tool.name == "BasePlot":
        # tool_response is a CallToolResult (type from mcp)
        # https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file#parsing-tool-results
        for content in tool_response.content:
            if isinstance(content, types.TextContent):
                # Convert BasePlot tool response (hex string) to bytes
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
                filename = "BasePlot.png"
                await tool_context.save_artifact(
                    filename=filename, artifact=artifact_part
                )
                return f"Plot created and saved as artifact: {filename}"

    # Passthrough for other tools or no matching content
    return None


plot_agent = LlmAgent(
    name="Plot",
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
Use the "Random" agent for generating random numbers and the "Plot" agent for plotting data.
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
