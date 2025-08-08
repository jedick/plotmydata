from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.models.lite_llm import LiteLlm
from google.adk import Agent
import os

"""Statistics agent for performing computations using R functions."""

# Optional: Filter specific tools
# tool_filter = ["rnorm"]

# Define the MCPToolset with connection parameters
url = os.environ["MCPGATEWAY_ENDPOINT"]
mcp_toolset = MCPToolset(
    connection_params=SseConnectionParams(url=url),
    # tool_filter = tool_filter,
)

instruction = """
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

root_agent = Agent(
    # If we're using the OpenAI API, get the value of OPENAI_MODEL_NAME set by entrypoint.sh
    # If we're using an OpenAI-compatible endpoint (Docker Model Runner), use a fake API key
    model=LiteLlm(
        model=os.environ.get("OPENAI_MODEL_NAME", ""),
        api_key=os.environ.get("OPENAI_API_KEY", "fake-API-key"),
    ),
    name="statistics_agent",
    instruction=instruction,
    tools=[mcp_toolset],
)
