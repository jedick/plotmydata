from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.base_tool import BaseTool
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import LlmAgent
from google.genai.types import Part
from typing import Dict, Any, Optional, Tuple
from mcp import types, StdioServerParameters
from prompts import Root, Session, Code
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


def detect_file_type(byte_data: bytes) -> Tuple[str, str]:
    """
    Detect file type from magic number/bytes and return (mime_type, file_extension).
    Supports BMP, JPEG, PNG, TIFF, and PDF.
    """
    if len(byte_data) < 8:
        # Default to PNG if we can't determine
        return "image/png", "png"

    # Check magic numbers
    if byte_data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", "png"
    elif byte_data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", "jpg"
    elif byte_data.startswith(b"BM"):
        return "image/bmp", "bmp"
    elif byte_data.startswith(b"II*\x00") or byte_data.startswith(b"MM\x00*"):
        return "image/tiff", "tiff"
    elif byte_data.startswith(b"%PDF"):
        return "application/pdf", "pdf"
    else:
        # Default to PNG if we can't determine
        return "image/png", "png"


async def save_plot_artifact(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict
) -> Optional[Dict]:
    """
    Callback function to save plot files returned from Plot() as an ADK artifact.
    """
    if tool.name in ["Plot"]:
        # tool_response is a CallToolResult (type from mcp)
        # https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file#parsing-tool-results
        for content in tool_response.content:
            if isinstance(content, types.TextContent):
                # Convert tool response (hex string) to bytes
                byte_data = bytes.fromhex(content.text)

                # Detect file type from magic number
                mime_type, file_extension = detect_file_type(byte_data)

                # Encode binary data to Base64 format
                encoded = base64.b64encode(byte_data).decode("utf-8")
                artifact_part = Part(
                    inline_data={
                        "data": encoded,
                        "mime_type": mime_type,
                    }
                )
                # TODO: Use unique filename
                filename = f"{tool.name}.{file_extension}"
                await tool_context.save_artifact(
                    filename=filename, artifact=artifact_part
                )
                return f"Plot created and saved as artifact: {filename}"

    # Passthrough for other tools or no matching content
    return None


# Create agent to run R code
code_agent = LlmAgent(
    name="Code",
    description="Agent for running R code and making plots.",
    model=model,
    instruction=Code,
    tools=[
        McpToolset(
            connection_params=connection_params,
            tool_filter=["Run", "Plot"],
        )
    ],
    after_tool_callback=save_plot_artifact,
)

# Create agent to handle R sessions
session_agent = LlmAgent(
    name="Session",
    description="Agent for listing and selecting R sessions.",
    model=model,
    instruction=Session,
    tools=[
        McpToolset(
            connection_params=connection_params,
            tool_filter=["list_r_sessions", "select_r_session"],
        )
    ],
)

# Create parent agent and assign children via sub_agents
root_agent = LlmAgent(
    name="Coordinator",
    description="I route requests to agents for managing R sessions or running R functions (including plotting).",
    model=model,
    instruction=Root,
    sub_agents=[
        session_agent,
        code_agent,
    ],
)
