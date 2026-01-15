from google.adk.plugins.save_files_as_artifacts_plugin import SaveFilesAsArtifactsPlugin
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.base_tool import BaseTool
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents import LlmAgent
from google.adk.models import LlmResponse, LlmRequest
from google.adk.models.lite_llm import LiteLlm
from google.adk.apps import App
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.types import CallToolResult, TextContent
from mcp.client.stdio import stdio_client
from typing import Dict, Any, Optional, Tuple
from prompts import Root, Run, Data, Plot, Install
import base64
import os

# Define MCP server parameters
server_params = StdioServerParameters(
    command="Rscript",
    args=[
        # Use --vanilla to ignore .Rprofile, which is meant for the R instance running mcp_session()
        "--vanilla",
        "server.R",
    ],
)
# STDIO transport to local R MCP server
connection_params = StdioConnectionParams(server_params=server_params, timeout=10)

# Define model
# If we're using the OpenAI API, get the value of OPENAI_MODEL_NAME set by entrypoint.sh
# If we're using an OpenAI-compatible endpoint (Docker Model Runner), use a fake API key
model = LiteLlm(
    model=os.environ.get("OPENAI_MODEL_NAME", ""),
    api_key=os.environ.get("OPENAI_API_KEY", "fake-API-key"),
)


async def select_r_session(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """
    Callback function to select the first R session.
    """
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.call_tool("select_r_session", {"session": 1})
            print("[select_r_session] R session selected!")
    # Return None to allow the LlmAgent's normal execution
    return None


async def catch_tool_errors(tool: BaseTool, args: dict, tool_context: ToolContext):
    """
    Callback function to catch errors from tool calls and turn them into a message.
    Modified from https://github.com/google/adk-python/discussions/795#discussioncomment-13460659
    """
    try:
        return await tool.run_async(args=args, tool_context=tool_context)
    except Exception as e:
        # Format the error as a tool response
        # https://github.com/google/adk-python/commit/4df926388b6e9ebcf517fbacf2f5532fd73b0f71
        response = CallToolResult(
            # The error has class McpError; use e.error.message to get the text
            content=[TextContent(type="text", text=e.error.message)],
            isError=True,
        )
        return response.model_dump(exclude_none=True, mode="json")


async def preprocess_artifact(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Callback function to copy the latest artifact to a temporary file.
    """

    # Callback and artifact handling code modified from:
    # https://google.github.io/adk-docs/callbacks/types-of-callbacks/#before-model-callback
    # https://github.com/google/adk-python/issues/2176#issuecomment-3395469070

    # Get the last user message in the request contents
    last_user_message = llm_request.contents[-1].parts[-1].text

    # Function call events have no text part, so set this to "" for string search in the next step
    if last_user_message is None:
        last_user_message = ""

    # If a file was uploaded then SaveFilesAsArtifactsPlugin() adds "[Uploaded Artifact: file_name.csv]" to the user message
    # Check for "Uploaded Artifact:" in the last user message
    if "Uploaded Artifact:" in last_user_message:

        # Add a text part only if there are any issues with accessing or saving the artifact
        added_text = ""
        # List available artifacts
        artifacts = await callback_context.list_artifacts()
        if len(artifacts) == 0:
            added_text = "No uploaded file is available"
        else:
            most_recent_file = artifacts[-1]
            try:
                # Get artifact and byte data
                artifact = await callback_context.load_artifact(
                    filename=most_recent_file
                )
                byte_data = artifact.inline_data.data
                # Save artifact as temporary file
                tmp_dir = "/tmp/uploads"
                tmp_file_path = os.path.join(tmp_dir, most_recent_file)
                # Write the file
                with open(tmp_file_path, "wb") as f:
                    f.write(byte_data)
                # Set appropriate permissions
                os.chmod(tmp_file_path, 0o644)
                print(f"[preprocess_artifact] Saved artifact as '{tmp_file_path}'")

            except Exception as e:
                added_text = f"Error processing artifact: {str(e)}"

        # If there were any issues, add a new part to the user message
        if added_text:
            # llm_request.contents[-1].parts.append(types.Part(text=added_text))
            llm_request.contents[0].parts.append(types.Part(text=added_text))
            print(
                f"[preprocess_artifact] Added text part to user message: '{added_text}'"
            )

    # Return None to allow the possibly modified request to go to the LLM
    return None


async def preprocess_messages(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Callback function to modify user messages to point to temporary artifact file paths.
    """

    # Changes to session state made by callbacks are not preserved across events
    # See: https://github.com/google/adk-docs/issues/904
    # Therefore, for every callback invocation we need to loop over all events, not just the most recent one
    for i in range(len(llm_request.contents)):
        # Inspect the user message in the request contents
        user_message = llm_request.contents[i].parts[-1].text
        if user_message:
            # Modify file path in user message
            # Original file path inserted by SaveFilesAsArtifactsPlugin():
            #   [Uploaded Artifact: "breast-cancer.csv"]
            # Modified file path used by preprocess_artifact():
            #   [Uploaded File: "/tmp/uploads/breast-cancer.csv"]
            tmp_dir = "/tmp/uploads/"
            if '[Uploaded Artifact: "' in user_message:
                user_message = user_message.replace(
                    '[Uploaded Artifact: "', f'[Uploaded File: "{tmp_dir}'
                )
                llm_request.contents[i].parts[-1].text = user_message
                print(f"[preprocess_messages] Modified user message: '{user_message}'")

    return None


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


async def skip_summarization_for_plot_success(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict
) -> Optional[Dict]:
    """
    Callback function to turn off summarization if plot succeeded.
    """

    # If there was an error making the plot, the LLM tells the user what happened.
    # This happens because skip_summarization is False by default.

    # But if the plot was created successfully, there's
    # no need for an extra LLM call to tell us it's there.
    if tool.name in ["make_plot", "make_ggplot"]:
        if not tool_response["isError"]:
            tool_context.actions.skip_summarization = True

    return None


async def save_plot_artifact(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict
) -> Optional[Dict]:
    """
    Callback function to save plot files as an ADK artifact.
    """

    # Look for plot tool (so we don't bother with transfer_to_agent or other functions)
    if tool.name in ["make_plot", "make_ggplot"]:
        # In ADK 1.17.0, tool_response is a dict (i.e. result of model_dump method invoked on MCP CallToolResult instance):
        # https://github.com/google/adk-python/commit/4df926388b6e9ebcf517fbacf2f5532fd73b0f71
        # https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file#parsing-tool-results
        if "content" in tool_response and not tool_response["isError"]:
            for content in tool_response["content"]:
                if "type" in content and content["type"] == "text":
                    # Convert tool response (hex string) to bytes
                    byte_data = bytes.fromhex(content["text"])

                    # Detect file type from magic number
                    mime_type, file_extension = detect_file_type(byte_data)

                    # Encode binary data to Base64 format
                    encoded = base64.b64encode(byte_data).decode("utf-8")
                    artifact_part = types.Part(
                        inline_data={
                            "data": encoded,
                            "mime_type": mime_type,
                        }
                    )
                    # Use second part of tool name (e.g. make_ggplot -> ggplot.png)
                    filename = f"{tool.name.split("_", 1)[1]}.{file_extension}"
                    await tool_context.save_artifact(
                        filename=filename, artifact=artifact_part
                    )
                    # Format the success message as a tool response
                    text = f"Plot created and saved as an artifact: {filename}"
                    response = CallToolResult(
                        content=[TextContent(type="text", text=text)],
                    )
                    return response.model_dump(exclude_none=True, mode="json")

    # Passthrough for other tools or no matching content (e.g. tool error)
    return None


# Create agent to run R code
run_agent = LlmAgent(
    name="Run",
    description="Runs R code without making plots. Use the `Run` agent for executing code that does not load data or make a plot.",
    model=model,
    instruction=Run,
    tools=[
        McpToolset(
            connection_params=connection_params,
            tool_filter=["run_visible", "run_hidden"],
        )
    ],
    before_model_callback=[preprocess_artifact, preprocess_messages],
    before_tool_callback=catch_tool_errors,
)

# Create agent to load data
data_agent = LlmAgent(
    name="Data",
    description="Loads data into an R data frame and summarizes it. Use the `Data` agent for loading data from a file or URL before making a plot.",
    model=model,
    instruction=Data,
    tools=[
        McpToolset(
            connection_params=connection_params,
            tool_filter=["run_visible"],
        )
    ],
    before_model_callback=[preprocess_artifact, preprocess_messages],
    before_tool_callback=catch_tool_errors,
)

# Create agent to make plots using R code
plot_agent = LlmAgent(
    name="Plot",
    description="Makes plots using R code. Use the `Plot` agent after loading any required data.",
    model=model,
    instruction=Plot,
    tools=[
        McpToolset(
            connection_params=connection_params,
            tool_filter=["make_plot", "make_ggplot"],
        )
    ],
    before_model_callback=[preprocess_artifact, preprocess_messages],
    before_tool_callback=catch_tool_errors,
    after_tool_callback=[skip_summarization_for_plot_success, save_plot_artifact],
)

# Create agent to install R packages
install_agent = LlmAgent(
    name="Install",
    description="Installs R packages. Use the `Install` agent when an R package needs to be installed.",
    model=model,
    instruction=Install,
    tools=[
        McpToolset(
            connection_params=connection_params,
            tool_filter=["run_visible"],
        )
    ],
    before_model_callback=[preprocess_artifact, preprocess_messages],
    before_tool_callback=catch_tool_errors,
)

# Create parent agent and assign children via sub_agents
root_agent = LlmAgent(
    name="Coordinator",
    # "Use the..." tells sub-agents to transfer to Coordinator for help requests
    description="Multi-agent system for performing actions in R. Use the `Coordinator` agent for getting help on packages, datasets, and functions.",
    model=model,
    instruction=Root,
    # To pass control back to root, the help and run functions should be tools or a ToolAgent (not sub_agent)
    tools=[
        McpToolset(
            connection_params=connection_params,
            tool_filter=["help_package", "help_topic"],
        )
    ],
    sub_agents=[
        run_agent,
        data_agent,
        plot_agent,
        install_agent,
    ],
    # Select R session
    before_agent_callback=select_r_session,
    # Save user-uploaded artifact as a temporary file and modify messages to point to this file
    before_model_callback=[preprocess_artifact, preprocess_messages],
    before_tool_callback=catch_tool_errors,
)

app = App(
    name="PlotMyData",
    root_agent=root_agent,
    # This inserts user messages like '[Uploaded Artifact: "breast-cancer.csv"]'
    plugins=[SaveFilesAsArtifactsPlugin()],
)
