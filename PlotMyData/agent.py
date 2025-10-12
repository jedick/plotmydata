from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.base_tool import BaseTool
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import LlmAgent
from google.genai.types import Part
from mcp import types, StdioServerParameters
from typing import Dict, Any, Optional
from prompts import Root, Random, Plot, Code, CSV
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

# Create agent for generating random numbers
random_agent = LlmAgent(
    name="Random",
    description="Agent for generating random numbers using R functions.",
    model=model,
    instruction=Random,
    tools=[
        # Define the toolset with MCP connection parameters
        McpToolset(
            connection_params=connection_params,
            # List tools for random numbers
            tool_filter=["Discrete", "Continuous"],
        )
    ],
)


# Callback function to save PNG returned from BasePlot() as an ADK artifact
async def save_plot_artifact(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict
) -> Optional[Dict]:
    if tool.name in ["BasePlot", "PlotCSV"]:
        # tool_response is a CallToolResult (type from mcp)
        # https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file#parsing-tool-results
        for content in tool_response.content:
            if isinstance(content, types.TextContent):
                # Convert tool response (hex string) to bytes
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
                filename = f"{tool.name}.png"
                await tool_context.save_artifact(
                    filename=filename, artifact=artifact_part
                )
                return f"Plot created and saved as artifact: {filename}"

    # Passthrough for other tools or no matching content
    return None


# Callback function to intercept CSV content before it reaches the LLM
async def before_model_callback(callback_context, content):
    """
    Intercept content before it reaches the LLM to filter out binary content
    that LiteLlm cannot handle, such as CSV file uploads.
    """
    from google.genai.types import Content, Part

    # Create a new content with only text parts
    filtered_parts = []

    for part in content.parts:
        # Only keep text parts, filter out inline_data (binary content)
        if hasattr(part, "text") and part.text:
            filtered_parts.append(Part(text=part.text))

    # If we have text parts, return the filtered content
    if filtered_parts:
        return Content(role=content.role, parts=filtered_parts)

    # If no text parts remain, return the original content
    return content


# Callback function to load CSV artifact and inject data into PlotCSV tool arguments
async def load_csv_artifact(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict]:
    if tool.name == "PlotCSV":
        # Check if csv_filename is provided in arguments
        csv_filename = args.get("csv_filename")
        if csv_filename:
            try:
                # Load the CSV artifact
                artifact = await tool_context.load_artifact(filename=csv_filename)
                if artifact and artifact.inline_data:
                    # Decode the CSV data from base64
                    csv_data = artifact.inline_data.data
                    # Remove csv_filename from args and add csv_data
                    args_with_data = args.copy()
                    del args_with_data["csv_filename"]
                    args_with_data["csv_data"] = csv_data
                    return args_with_data
                else:
                    return {
                        "error": f"CSV file '{csv_filename}' not found in artifacts"
                    }
            except Exception as e:
                return {"error": f"Failed to load CSV artifact '{csv_filename}': {e}"}

    # Passthrough for other tools or no csv_filename provided
    return None


# Create agent for making scatterplots
plot_agent = LlmAgent(
    name="Plot",
    description="Agent for making scatterplots using R.",
    model=model,
    instruction=Plot,
    tools=[
        McpToolset(
            connection_params=connection_params,
            tool_filter=["BasePlot"],
        )
    ],
    after_tool_callback=save_plot_artifact,
)

# Create agent to run R code
code_agent = LlmAgent(
    name="Code",
    description="Agent for running R code.",
    model=model,
    instruction=Code,
    tools=[
        McpToolset(
            connection_params=connection_params,
            tool_filter=["Run"],
        )
    ],
)

# Create agent for plotting CSV data
csv_agent = LlmAgent(
    name="CSV",
    description="Agent for plotting data from uploaded CSV files.",
    model=model,
    instruction=CSV,
    tools=[
        McpToolset(
            connection_params=connection_params,
            tool_filter=["PlotCSV"],
        )
    ],
    before_model_callback=before_model_callback,
    before_tool_callback=load_csv_artifact,
    after_tool_callback=save_plot_artifact,
)

# Create parent agent and assign children via sub_agents
root_agent = LlmAgent(
    name="Coordinator",
    description="I route requests to agents for generating random numbers, plotting data, or plotting CSV files using R functions.",
    model=model,
    instruction=Root,
    sub_agents=[
        random_agent,
        plot_agent,
        code_agent,
        csv_agent,
    ],
)
