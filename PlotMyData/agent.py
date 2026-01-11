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
from prompts import Root, Run, Data, Plot
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
    Callback function to copy artifact to temporary file and inject file path into user message.
    """

    # Callback and artifact handling code modified from:
    # https://google.github.io/adk-docs/callbacks/types-of-callbacks/#before-model-callback
    # https://github.com/google/adk-python/issues/2176#issuecomment-3395469070

    # Inspect the last user message in the request contents
    try:
        # last_user_message = llm_request.contents[-1].parts[-1].text
        last_user_message = llm_request.contents[0].parts[-1].text
    except:
        last_user_message = None
    # If a file was uploaded then last_user_message should be e.g. "[Uploaded Artifact: file_name]"
    # (message part added by SaveFilesAsArtifactsPlugin())
    print(f"[preprocess_artifact] Inspecting last user message: '{last_user_message}'")

    # Check for user message
    if last_user_message is not None:

        # We'll only add a text part if artifact isn't available or can't be saved
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
                upload_dir = "/tmp/uploads"
                file_name = artifact.inline_data.display_name
                file_path = os.path.join(upload_dir, file_name)
                # Write the file
                with open(file_path, "wb") as f:
                    f.write(byte_data)
                # Set appropriate permissions
                os.chmod(file_path, 0o644)
                # Inject temporary file path into user message
                # original: [Uploaded Artifact: file_name] (as inserted by SaveFilesAsArtifactsPlugin())
                # modified: [Uploaded File: file_path]
                modified_text = last_user_message.replace(file_name, file_path)
                modified_text = modified_text.replace(
                    "Uploaded Artifact", "Uploaded File"
                )

                # llm_request.contents[-1].parts[-1].text = modified_text
                llm_request.contents[0].parts[-1].text = modified_text
                print(f"[preprocess_artifact] Modified user message: '{modified_text}'")

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
    Callback function to save plot files as an ADK artifact.
    """
    # We just want to see the plot in the conversation;
    # no need for an extra LLM call to tell us it's there.
    # This also prevents the model from trying to rerun the code,
    # so we can directly show the error message.
    tool_context.actions.skip_summarization = True

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
    # TODO: Only use this callback in the root agent if changes to LlmRequest are persistent
    # https://github.com/google/adk-python/issues/2576
    before_model_callback=preprocess_artifact,
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
    before_model_callback=preprocess_artifact,
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
    before_model_callback=preprocess_artifact,
    before_tool_callback=catch_tool_errors,
    after_tool_callback=save_plot_artifact,
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
    ],
    # Select R session
    before_agent_callback=select_r_session,
    # Save user-uploaded artifact as a temporary file to be accessed by R code
    before_model_callback=preprocess_artifact,
    before_tool_callback=catch_tool_errors,
)

app = App(
    name="PlotMyData",
    root_agent=root_agent,
    # This inserts user messages like '[Uploaded Artifact: "breast-cancer.csv"]'
    plugins=[SaveFilesAsArtifactsPlugin()],
)
